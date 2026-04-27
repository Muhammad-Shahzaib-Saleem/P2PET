"""
transfer_endpoint.py
────────────────────
Drop-in addition to your existing main.py.

Paste the imports at the top of main.py (if not already present),
then paste the helpers + endpoints after your existing route definitions.

Flow when POST /transfer is called:
  1. Read result.json  →  list of {buyer_id, seller_id, energy_matched, price}
  2. Map each Ethereum address → Pi IP using pis.json (eth_address field)
  3. For every match, call POST /transfer/start on the SELLER's Pi meter API
  4. Poll GET /transfer/status on seller Pi until relay closes (energy delivered)
  5. All matches run in parallel via ThreadPoolExecutor
  6. Return a per-match summary
"""

# ─── Extra imports (add to top of main.py if not already there) ──────────────
import concurrent.futures
from typing import List, Dict, Any

# ─── Constants ────────────────────────────────────────────────────────────────

RESULT_FILE              = "match_result.json"   # matching algorithm output
PIS_JSON_PATH            = "pis.json"      # must include "eth_address" per Pi
METER_API_PORT           = 8002            # default meter_api port on each Pi
TRANSFER_POLL_INTERVAL_S = 2              # seconds between status polls
TRANSFER_TIMEOUT_S       = 300            # 5-minute hard timeout per transfer


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_result_json(path: str = RESULT_FILE) -> List[Dict]:
    """Load the matching result produced by the bidding algorithm."""
    with open(path, "r") as f:
        return json.load(f)


def build_address_to_pi_map(pis_json_path: str = PIS_JSON_PATH) -> Dict[str, Dict]:
    """
    Returns: { "0xaddress_lowercase": {"name": ..., "hostname": ..., "meter_port": ...} }
    Built from the eth_address field in every pis.json entry.
    """
    with open(pis_json_path, "r") as f:
        pis: Dict = json.load(f)

    mapping = {}
    for name, info in pis.items():
        addr = info.get("eth_address", "").lower()
        if addr:
            mapping[addr] = {
                "name":       name,
                "hostname":   info["hostname"],
                "meter_port": info.get("meter_port", METER_API_PORT),
            }
    return mapping


def meter_url(hostname: str, port: int) -> str:
    return f"http://{hostname}:{port}"


def pi_start_transfer(seller_info: Dict, buyer_hostname: str, energy_kwh: float) -> Dict:
    """POST /transfer/start on the seller Pi to open its relay."""
    url = f"{meter_url(seller_info['hostname'], seller_info['meter_port'])}/transfer/start"
    payload = {
        "from_pi_ip":   seller_info["hostname"],
        "to_pi_ip":     buyer_hostname,
        "transfer_kwh": energy_kwh,
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def pi_poll_transfer_status(seller_info: Dict, timeout_s: int = TRANSFER_TIMEOUT_S) -> Dict:
    """
    Polls GET /transfer/status on the seller Pi until active == False,
    then returns the final status dict.
    Hard-stops and closes the relay if timeout_s is exceeded.
    """
    url     = f"{meter_url(seller_info['hostname'], seller_info['meter_port'])}/transfer/status"
    elapsed = 0

    while elapsed < timeout_s:
        resp   = requests.get(url, timeout=10)
        resp.raise_for_status()
        status = resp.json()

        if not status.get("active", True):
            return status

        time.sleep(TRANSFER_POLL_INTERVAL_S)
        elapsed += TRANSFER_POLL_INTERVAL_S

    # Timed out — attempt graceful relay close
    try:
        requests.post(
            f"{meter_url(seller_info['hostname'], seller_info['meter_port'])}/transfer/stop",
            json={"from_pi_ip": seller_info["hostname"], "to_pi_ip": "", "transfer_kwh": 0},
            timeout=10,
        )
    except Exception:
        pass

    return {"active": False, "stop_reason": "timeout", "relay_on": False}


def execute_single_match(match: Dict, addr_map: Dict) -> Dict:
    """
    Runs one buyer<->seller match end-to-end (blocking).
    Called inside a thread-pool so all matches run in parallel.
    """
    buyer_addr  = match["buyer_id"].lower()
    seller_addr = match["seller_id"].lower()
    energy_kwh  = match["energy_matched"]
    price       = match["price"]

    result = {
        "buyer":           match["buyer_id"],
        "seller":          match["seller_id"],
        "energy_kwh":      energy_kwh,
        "price":           price,
        "transfer_status": None,
        "error":           None,
    }

    # 1. Resolve Pi info from address map
    seller_info = addr_map.get(seller_addr)
    buyer_info  = addr_map.get(buyer_addr)

    if not seller_info:
        result["error"] = f"Seller {match['seller_id']} not found in pis.json"
        return result
    if not buyer_info:
        result["error"] = f"Buyer {match['buyer_id']} not found in pis.json"
        return result

    print(f"[transfer] {seller_info['name']} -> {buyer_info['name']}  {energy_kwh} kWh @ {price}")

    # 2. Start transfer on seller Pi
    try:
        start_resp = pi_start_transfer(seller_info, buyer_info["hostname"], energy_kwh)
        print(f"[transfer] started: {start_resp}")
    except Exception as e:
        result["error"] = f"Failed to start transfer on {seller_info['name']}: {e}"
        return result

    # 3. Poll until relay closes (energy delivered)
    try:
        final_status = pi_poll_transfer_status(seller_info)
        result["transfer_status"] = final_status
        stop_reason = final_status.get("stop_reason", "completed")
        print(f"[transfer] done ({stop_reason}): {seller_info['name']} -> {buyer_info['name']}")
    except Exception as e:
        result["error"] = f"Error polling transfer status: {e}"

    return result


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/transfer")
def transfer_energy():
    """
    Reads result.json and executes all energy transfers in parallel.
    For each match: opens seller relay -> polls until energy delivered -> closes relay.
    Returns a per-match summary.
    """
    try:
        matches = load_result_json(RESULT_FILE)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{RESULT_FILE} not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in {RESULT_FILE}: {e}")

    if not matches:
        return {"status": "no_matches", "results": []}

    try:
        addr_map = build_address_to_pi_map(PIS_JSON_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pis.json not found")

    results: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(matches)) as pool:
        futures = {
            pool.submit(execute_single_match, match, addr_map): match
            for match in matches
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                original = futures[future]
                results.append({
                    "buyer":  original.get("buyer_id"),
                    "seller": original.get("seller_id"),
                    "error":  str(e),
                })

    success_count = sum(
        1 for r in results
        if r.get("error") is None
        and r.get("transfer_status", {}).get("stop_reason") != "timeout"
    )

    return {
        "status":        "completed",
        "total_matches": len(matches),
        "succeeded":     success_count,
        "failed":        len(matches) - success_count,
        "results":       results,
    }


@app.get("/transfer/status/{seller_hostname}")
def get_transfer_status_for_pi(seller_hostname: str):
    """
    Proxy GET /transfer/status from a specific seller Pi by hostname/IP.
    Useful for checking progress of an ongoing transfer.
    """
    try:
        with open(PIS_JSON_PATH) as f:
            pis = json.load(f)

        port = METER_API_PORT
        for info in pis.values():
            if info.get("hostname") == seller_hostname:
                port = info.get("meter_port", METER_API_PORT)
                break

        resp = requests.get(f"http://{seller_hostname}:{port}/transfer/status", timeout=10)
        resp.raise_for_status()
        return resp.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))