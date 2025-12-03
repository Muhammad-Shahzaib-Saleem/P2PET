import json, os, subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from eth_account import Account
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from dotenv import load_dotenv
from fetch_and_match import run_matching_and_get_hash

load_dotenv()
app = FastAPI(title="Dynamic P2P Blockchain API")

# ======================================================
# 1️⃣ Load Pi mapping
# ======================================================
with open("pis.json", "r") as f:
    PIS = json.load(f)

def find_pi(target: str):
    """Find Pi entry from pis.json by host or hostname"""
    for pi in PIS:
        if target == pi["host"] or target == pi["hostname"]:
            return pi
    return None

def build_rpc_url(pi, base_port=22000):
    """Construct RPC URL using Pi hostname + calculated port"""
    num = int(''.join(filter(str.isdigit, pi["host"]))) if any(ch.isdigit() for ch in pi["host"]) else 0
    return f"http://{pi['hostname']}:{base_port + num}"

# ======================================================
# 2️⃣ Web3 + Contract loader
# ======================================================
def get_web3_and_contract_for_pi(pi):
    """Build Web3, Account, and Contract objects dynamically"""
    rpc_url = build_rpc_url(pi)
    print(f"🔗 Connecting to {pi['host']} ({pi['hostname']}) → {rpc_url}")

    CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")
    ABI_PATH = os.getenv("ABI_PATH")
    ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")

    with open(CONTRACT_ADDRESS_PATH) as f:
        CONTRACT_ADDRESS = json.load(f)["contract_address"]

    with open(ABI_PATH) as f:
        abi = json.load(f)

    keystore = subprocess.check_output(
        "cd ../../quorum-ibft-chain/node*/data/keystore; cat $(ls | head -n 1)",
        shell=True, text=True
    ).strip()

    PRIVATE_KEY = Account.decrypt(keystore, ACCOUNT_PASSWORD).hex()

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    account = w3.eth.account.from_key(PRIVATE_KEY)
    contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

    return w3, account, contract, PRIVATE_KEY


def send_transaction(w3, account, private_key, function_call):
    """Generic blockchain transaction sender"""
    nonce = w3.eth.get_transaction_count(account.address)
    tx = function_call.build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": 0
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt


# ======================================================
# 3️⃣ Request models for Frontend
# ======================================================
class HostModel(BaseModel):
    host: str

class SubmitDataModel(BaseModel):
    host: str
    role: int
    energy: int
    price: int


# ======================================================
# 4️⃣ API ROUTES
# ======================================================

@app.get("/")
def home():
    return {
        "status": True,
        "message": "P2P Energy Trading API ready",
        "available_nodes": [pi["host"] for pi in PIS]
    }

@app.get("/nodes")
def list_nodes():
    return {"pis": PIS}

@app.post("/connect")
def connect_to_pi(data: HostModel):
    """Frontend sends host name → backend returns Pi info + RPC URL"""
    pi = find_pi(data.host)
    if not pi:
        raise HTTPException(status_code=404, detail=f"No Pi found for host '{data.host}'")
    rpc_url = build_rpc_url(pi)
    return {"status": True, "host": pi["host"], "hostname": pi["hostname"], "rpc_url": rpc_url}


@app.post("/register")
def register_pi(data: HostModel):
    """Register participant for selected Pi"""
    pi = find_pi(data.host)
    if not pi:
        raise HTTPException(status_code=404, detail=f"No Pi found for host '{data.host}'")

    w3, acc, contract, pk = get_web3_and_contract_for_pi(pi)
    receipt = send_transaction(w3, acc, pk, contract.functions.register())
    return {"status": receipt.status == 1, "node": pi["host"]}


@app.post("/submit-data")
def submit_data(data: SubmitDataModel):
    """Submit energy/price data for selected Pi"""
    pi = find_pi(data.host)
    if not pi:
        raise HTTPException(status_code=404, detail=f"No Pi found for host '{data.host}'")

    w3, acc, contract, pk = get_web3_and_contract_for_pi(pi)
    receipt = send_transaction(
        w3, acc, pk, contract.functions.submitData(data.role, data.energy, data.price)
    )
    return {"status": receipt.status == 1, "node": pi["host"]}


@app.post("/submit-execution-result")
def submit_execution_result(data: HostModel):
    """Run matching + submit result for selected Pi"""
    pi = find_pi(data.host)
    if not pi:
        raise HTTPException(status_code=404, detail=f"No Pi found for host '{data.host}'")

    w3, acc, contract, pk = get_web3_and_contract_for_pi(pi)
    result_hash = run_matching_and_get_hash(contract)

    receipt = send_transaction(
        w3, acc, pk, contract.functions.submitExecutionResult(Web3.to_bytes(hexstr=result_hash))
    )
    return {"status": receipt.status == 1, "node": pi["host"]}


# ======================================================
# 5️⃣ Server Runner
# ======================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
