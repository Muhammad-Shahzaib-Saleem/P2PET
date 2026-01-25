#!/usr/bin/env python3
"""
FastMCP Server for P2P Energy Trading & Home Automation
Exposes blockchain energy trading and fan control APIs to LLM clients via MCP protocol
"""
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from pathlib import Path
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo
import pickle
import httpx
import json

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# ========== CRASH VISIBILITY HOOK ==========
import traceback
def excepthook(type, value, tb):
    traceback.print_exception(type, value, tb, file=sys.stderr)
sys.excepthook = excepthook
# ===========================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="P2PEnergyTradingAndHomeAutomation",
    instructions="""
    This server provides:
    1. P2P Energy Trading on Blockchain - Register participants, submit trades, manage trading rounds
    2. Fan Control - Turn fan on/off via GPIO relay (pin 17)
    3. Google Calendar - Schedule meetings and check availability
    
    P2P Energy Trading System:
    - 3-phase trading rounds: DataSubmission → Execution → Trading
    - Participants can be buyers or sellers of energy
    - Blockchain-based verification and settlement
    """
)

# Global state for fan status
fan_status = {"is_on": False, "last_action": None}

# ---------------- P2P Energy Trading Configuration ----------------

# Load Pi configuration
_PROJECT_ROOT = Path(__file__).resolve().parent
_PIS_JSON = _PROJECT_ROOT / "pis.json"

def _load_pis_config() -> Dict[str, Any]:
    """Load Raspberry Pi configuration from pis.json"""
    try:
        if _PIS_JSON.exists():
            with open(_PIS_JSON, "r") as f:
                pis = json.load(f)
                # pis.json is keyed by IP, convert to be keyed by host for easier lookup
                return {pi_data["host"]: pi_data for pi_data in pis.values()}
        return {}
    except Exception as e:
        logger.error(f"Failed to load pis.json: {e}")
        return {}

# Default API base URL (will be constructed dynamically based on hostname)
DEFAULT_API_PORT = 8000

# ---------------- P2P Energy Trading Tools ----------------

async def _call_api(endpoint: str, method: str = "GET", hostname: Optional[str] = None, api_hostname: Optional[str] = None, **params) -> Dict[str, Any]:
    """
    Helper to call P2P Energy Trading API endpoints
    
    Args:
        endpoint: API endpoint path (e.g., "/total_participants")
        method: HTTP method (GET or POST)
        hostname: Target Pi hostname (NOT USED FOR NOW - we use localhost)
        api_hostname: IP address to pass as 'hostname' parameter to API (for endpoints that need it)
        **params: Query parameters or JSON body data
    """
    try:
        # For now, always use localhost since main.py runs on Mac, not on Pis
        base_url = f"http://localhost:{DEFAULT_API_PORT}"
        
        url = f"{base_url}{endpoint}"
        
        # If api_hostname provided, add it to params (this is the IP that main.py expects)
        if api_hostname:
            params['hostname'] = api_hostname
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, params=params)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException:
        return {"error": f"Request timeout to {url}"}
    except httpx.HTTPError as e:
        return {"error": f"HTTP error: {str(e)}"}
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return {"error": str(e)}


@mcp.tool
async def p2p_register_participant(hostname: str) -> Dict[str, Any]:
    """
    Register a participant on the blockchain for P2P energy trading.
    Each participant must register before they can submit bids/offers.
    
    Args:
        hostname: Pi hostname from pis.json (e.g., "pi_2", "pi_4", etc.)
    
    Returns:
        Registration status with transaction hash if successful
    """
    logger.info(f"Registering participant on {hostname}")
    
    # Get Pi config to extract IP address
    pis_config = _load_pis_config()
    if hostname not in pis_config:
        return {"error": f"Hostname {hostname} not found in pis.json"}
    
    pi_ip = pis_config[hostname]["hostname"]  # This is actually the IP address
    
    # Call API with IP address as the hostname parameter (API expects IP)
    result = await _call_api("/dynamic_register", method="POST", hostname=hostname, api_hostname=pi_ip)
    return result


@mcp.tool
async def p2p_submit_trade(
    hostname: str,
    role: str,
    energy: int,
    price: int
) -> Dict[str, Any]:
    """
    Submit a bid (buyer) or offer (seller) for energy trading.
    Must be in DataSubmission phase (phase 0) of the trading round.
    
    Args:
        hostname: Pi hostname from pis.json
        role: "buyer" or "seller"
        energy: Amount of energy in kWh (will be scaled by 100 internally)
        price: Price per kWh in currency units (will be scaled by 100 internally)
    
    Returns:
        Transaction status and hash
    
    Example:
        - Buyer wants 10 kWh at 50 per kWh: role="buyer", energy=10, price=50
        - Seller offers 15 kWh at 45 per kWh: role="seller", energy=15, price=45
    """
    logger.info(f"Submitting trade on {hostname}: {role} {energy}kWh @ {price}")
    
    if role.lower() not in ["buyer", "seller"]:
        return {"error": "Invalid role. Must be 'buyer' or 'seller'"}
    
    # Get Pi config to extract IP address
    pis_config = _load_pis_config()
    if hostname not in pis_config:
        return {"error": f"Hostname {hostname} not found in pis.json"}
    
    pi_ip = pis_config[hostname]["hostname"]
    
    result = await _call_api(
        "/dynamic_submit_data",
        method="POST",
        hostname=hostname,
        api_hostname=pi_ip,
        role=role,
        energy=energy,
        price=price
    )
    return result


@mcp.tool
async def p2p_get_participants() -> Dict[str, Any]:
    """
    Get list of all registered participants in the P2P energy trading system.
    
    Returns:
        List of participant addresses registered on the blockchain
    """
    logger.info("Fetching participants list")
    result = await _call_api("/participants_list", method="GET")
    return result


@mcp.tool
async def p2p_get_total_participants() -> Dict[str, Any]:
    """
    Get total count of registered participants.
    
    Returns:
        Total number of participants
    """
    result = await _call_api("/total_participants", method="GET")
    return result


@mcp.tool
async def p2p_get_current_phase() -> Dict[str, Any]:
    """
    Get the current phase of the trading round.
    
    Phases:
        0 = DataSubmission - participants submit bids/offers
        1 = Execution - DA algorithm runs off-chain
        2 = Trading - physical energy trading occurs
    
    Returns:
        Current phase name and number
    """
    result = await _call_api("/current_phase", method="GET")
    return result


@mcp.tool
async def p2p_get_current_round() -> Dict[str, Any]:
    """
    Get the current trading round number.
    
    Returns:
        Current round number
    """
    result = await _call_api("/current_round", method="GET")
    return result


@mcp.tool
async def p2p_advance_phase(hostname: str) -> Dict[str, Any]:
    """
    Advance to the next phase in the trading round.
    Transitions: DataSubmission → Execution → Trading → DataSubmission (new round)
    
    Args:
        hostname: Pi hostname that will trigger the phase advance
    
    Returns:
        New phase information and transaction hash
    """
    logger.info(f"Advancing phase from {hostname}")
    
    # Get Pi config to extract IP address
    pis_config = _load_pis_config()
    if hostname not in pis_config:
        return {"error": f"Hostname {hostname} not found in pis.json"}
    
    pi_ip = pis_config[hostname]["hostname"]
    
    result = await _call_api("/dynamic_advance_phase", method="POST", hostname=hostname, api_hostname=pi_ip)
    return result


@mcp.tool
async def p2p_hash_participants(hostname: str) -> Dict[str, Any]:
    """
    Calculate and store hash of current participants' submitted data.
    Should be called at the end of DataSubmission phase.
    
    Args:
        hostname: Pi hostname that will trigger the hash calculation
    
    Returns:
        Computed hash and transaction details
    """
    logger.info(f"Hashing participants data from {hostname}")
    
    # Get Pi config to extract IP address
    pis_config = _load_pis_config()
    if hostname not in pis_config:
        return {"error": f"Hostname {hostname} not found in pis.json"}
    
    pi_ip = pis_config[hostname]["hostname"]
    
    result = await _call_api("/Dynamic_hash_participants", method="POST", hostname=hostname, api_hostname=pi_ip)
    return result


@mcp.tool
async def p2p_get_contract_address() -> Dict[str, Any]:
    """
    Get the deployed smart contract address on the blockchain.
    
    Returns:
        Smart contract address
    """
    result = await _call_api("/contract", method="GET")
    return result


@mcp.tool
async def p2p_list_available_pis() -> Dict[str, Any]:
    """
    List all configured Raspberry Pi nodes from pis.json.
    
    Returns:
        Dictionary of all configured Pi nodes with their hostnames and node numbers
    """
    pis_config = _load_pis_config()
    if not pis_config:
        return {"error": "No Pi configuration found", "pis": []}
    
    return {
        "total": len(pis_config),
        "pis": [
            {
                "host": host,
                "hostname": info["hostname"],
                "node_num": info["node_num"]
            }
            for host, info in pis_config.items()
        ]
    }


# ---------------- Google Calendar Integration ----------------

GCAL_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

_SECRETS_DIR = _PROJECT_ROOT / ".secrets" / "google"
_SECRETS_DIR.mkdir(parents=True, exist_ok=True)

_GCAL_CREDENTIALS = (_SECRETS_DIR / "credentials.json")
if not _GCAL_CREDENTIALS.exists():
    alt = _PROJECT_ROOT / "client_secret.json"
    if alt.exists():
        _GCAL_CREDENTIALS = alt

_GCAL_TOKEN = _SECRETS_DIR / "token.pkl"


def _gcal_service():
    """Return authorized Google Calendar API service."""
    creds = None

    if _GCAL_TOKEN.exists():
        try:
            with open(_GCAL_TOKEN, "rb") as f:
                creds = pickle.load(f)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and getattr(creds, "refresh_token", None):
            creds.refresh(Request())
            with open(_GCAL_TOKEN, "wb") as f:
                pickle.dump(creds, f)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_GCAL_CREDENTIALS), GCAL_SCOPES)
            creds = flow.run_local_server(port=0)
            with open(_GCAL_TOKEN, "wb") as f:
                pickle.dump(creds, f)

    return build("calendar", "v3", credentials=creds)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


# ----------------- GOOGLE CALENDAR TOOLS -----------------

@mcp.tool
def gcal_list_free_slots(
    date: str,
    duration_minutes: int,
    tz: str = "Asia/Karachi",
    start_hour: int = 9,
    end_hour: int = 18,
    calendar_id: str = "w1Lbs34yoWcBAwy17"
) -> List[Dict[str, Any]]:
    """
    List free slots for a specific date within a working window.
    """
    svc = _gcal_service()
    tzinfo = ZoneInfo(tz)

    day = datetime.strptime(date, "%Y-%m-%d").date()
    start_dt = datetime.combine(day, dtime(hour=start_hour), tzinfo)
    end_dt = datetime.combine(day, dtime(hour=end_hour), tzinfo)

    body = {
        "timeMin": _iso(start_dt),
        "timeMax": _iso(end_dt),
        "items": [{"id": calendar_id}],
        "timeZone": tz,
    }

    fb = svc.freebusy().query(body=body).execute()
    busy = fb["calendars"][calendar_id].get("busy", [])

    busy_ints = [(_parse_iso(b["start"]), _parse_iso(b["end"])) for b in busy]
    busy_ints.sort(key=lambda x: x[0])

    free = []
    cur = start_dt
    for bstart, bend in busy_ints:
        if bstart > cur:
            free.append((cur, min(bstart, end_dt)))
        cur = max(cur, bend)
        if cur >= end_dt:
            break

    if cur < end_dt:
        free.append((cur, end_dt))

    slots: List[Dict[str, str]] = []
    delta = timedelta(minutes=duration_minutes)

    for fstart, fend in free:
        s = fstart
        while s + delta <= fend:
            slots.append({"start": _iso(s), "end": _iso(s + delta)})
            s += delta

    return slots


@mcp.tool
def gcal_create_event(
    title: str,
    start_iso: str,
    duration_minutes: int,
    attendees: Optional[List[str]] = None,
    description: str = "",
    calendar_id: str = "primary",
    make_meet: bool = True
) -> Dict[str, Any]:
    """
    Create an event with optional Google Meet link.
    """
    svc = _gcal_service()

    start_dt = _parse_iso(start_iso)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": _iso(start_dt)},
        "end": {"dateTime": _iso(end_dt)},
    }

    if attendees:
        event["attendees"] = [{"email": e} for e in attendees]

    if make_meet:
        event["conferenceData"] = {
            "createRequest": {"requestId": f"mcp-{int(datetime.now().timestamp())}"}
        }

    created = svc.events().insert(
        calendarId=calendar_id,
        body=event,
        conferenceDataVersion=1 if make_meet else 0,
        sendUpdates="all",
    ).execute()

    return {
        "id": created.get("id"),
        "htmlLink": created.get("htmlLink"),
        "hangoutLink": created.get("hangoutLink"),
        "start": created.get("start"),
        "end": created.get("end"),
        "attendees": created.get("attendees", []),
    }


# ----------------- FAN CONTROL TOOLS -----------------

@mcp.tool
def turn_fan_on() -> Dict[str, Any]:
    logger.info("=== TURN_FAN_ON CALLED ===")
    try:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(17, GPIO.OUT)
        except (ImportError, RuntimeError):
            import fakerpigpio as GPIO
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(17, GPIO.OUT)

        GPIO.output(17, GPIO.LOW)

        fan_status["is_on"] = True
        fan_status["last_action"] = "turned_on"

        return {
            "status": "success",
            "message": "Fan turned ON",
            "fan_state": "on",
        }

    except Exception as e:
        logger.error(f"Error turning fan on: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool
def turn_fan_off() -> Dict[str, Any]:
    try:
        try:
            import RPi.GPIO as GPIO
            if not hasattr(turn_fan_off, "_gpio_setup"):
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(17, GPIO.OUT)
                turn_fan_off._gpio_setup = True
        except (ImportError, RuntimeError):
            import fakerpigpio as GPIO
            if not hasattr(turn_fan_off, "_gpio_setup"):
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(17, GPIO.OUT)
                turn_fan_off._gpio_setup = True

        GPIO.output(17, GPIO.HIGH)
        fan_status["is_on"] = False
        fan_status["last_action"] = "turned_off"

        return {
            "status": "success",
            "message": "Fan turned OFF",
            "fan_state": "off",
        }

    except Exception as e:
        logger.error(f"Error turning fan off: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool
def get_fan_status() -> Dict[str, Any]:
    try:
        try:
            import RPi.GPIO as GPIO
            if not hasattr(get_fan_status, "_gpio_setup"):
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(17, GPIO.OUT)
                get_fan_status._gpio_setup = True
            pin_state = GPIO.input(17)
        except (ImportError, RuntimeError):
            import fakerpigpio as GPIO
            if not hasattr(get_fan_status, "_gpio_setup"):
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(17, GPIO.OUT)
                get_fan_status._gpio_setup = True
            pin_state = GPIO.input(17)

        actual_state = "off" if pin_state else "on"

        return {
            "status": "success",
            "fan_state": actual_state,
            "is_on": fan_status["is_on"],
            "last_action": fan_status["last_action"],
        }

    except Exception as e:
        logger.error(f"Error getting fan status: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool
def cleanup_gpio() -> Dict[str, Any]:
    try:
        try:
            import RPi.GPIO as GPIO
        except (ImportError, RuntimeError):
            import fakerpigpio as GPIO

        GPIO.cleanup()
        return {"status": "success", "message": "GPIO cleanup completed"}

    except Exception as e:
        logger.error(f"GPIO cleanup failed: {e}")
        return {"status": "error", "message": str(e)}


# ---------------- MAIN -----------------

def main():
    print("PWD:", Path.cwd(), file=sys.stderr)
    print("FILES:", list(Path.cwd().iterdir()), file=sys.stderr)
    logger.info("=" * 70)
    logger.info("🚀 Starting P2P Energy Trading & Home Automation MCP Server")
    logger.info("=" * 70)
    logger.info("\n📦 P2P Energy Trading Tools:")
    logger.info("  - p2p_register_participant")
    logger.info("  - p2p_submit_trade")
    logger.info("  - p2p_get_participants")
    logger.info("  - p2p_get_total_participants")
    logger.info("  - p2p_get_current_phase")
    logger.info("  - p2p_get_current_round")
    logger.info("  - p2p_advance_phase")
    logger.info("  - p2p_hash_participants")
    logger.info("  - p2p_get_contract_address")
    logger.info("  - p2p_list_available_pis")
    logger.info("\n🌐 Google Calendar Tools:")
    logger.info("  - gcal_list_free_slots")
    logger.info("  - gcal_create_event")
    logger.info("\n💨 Fan Control Tools:")
    logger.info("  - turn_fan_on")
    logger.info("  - turn_fan_off")
    logger.info("  - get_fan_status")
    logger.info("  - cleanup_gpio")
    logger.info("=" * 70 + "\n")

    try:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except (ImportError, RuntimeError):
            import fakerpigpio as GPIO
            GPIO.cleanup()
    except Exception as e:
        logger.warning(f"GPIO cleanup warning: {e}")

    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
