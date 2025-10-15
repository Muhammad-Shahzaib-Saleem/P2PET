import subprocess
import os
import time
import json
import socket
import asyncio
from fastapi import FastAPI, HTTPException
from eth_account import Account
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from web3.exceptions import ContractLogicError
from dotenv import load_dotenv
from fetch_and_match import run_matching_and_get_hash

load_dotenv()

# ============================================================
#                 INITIAL SETUP
# ============================================================
app = FastAPI(title="P2P Energy Trading API (Hostname-based)")

# Load Pis
with open("pis.json", "r") as f:
    PIS = json.load(f)

# Build semaphore per hostname (so each Pi handles 1 request at a time)
pi_semaphores = {pi["hostname"]: asyncio.Semaphore(1) for pi in PIS}

# Common configuration
LOCAL_PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")
ABI_PATH = os.getenv("ABI_PATH")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")

# Read contract info
with open(CONTRACT_ADDRESS_PATH, "r") as f:
    CONTRACT_ADDRESS = json.load(f)["contract_address"]

with open(ABI_PATH, "r") as f:
    ABI = json.load(f)

# ============================================================
#                 PRIVATE KEY DECRYPTION
# ============================================================
try:
    keystore = subprocess.check_output(
        "cd ..; cd ..; cd quorum-ibft-chain; cd node*; cd data/keystore; cat $(ls | head -n 1)",
        shell=True,
        text=True,
    ).strip()

    private_key_bytes = Account.decrypt(keystore, ACCOUNT_PASSWORD)
    PRIVATE_KEY = private_key_bytes.hex()
except Exception as e:
    raise RuntimeError(f"Failed to decrypt private key: {e}")

account = Account.from_key(PRIVATE_KEY)
sender_address = account.address

# ============================================================
#                 HELPER FUNCTIONS
# ============================================================

def get_web3_for_pi(hostname: str) -> Web3:
    """Return a Web3 instance for the Pi node identified by hostname."""
    rpc_url = f"http://{hostname}:22000"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def send_transaction(w3: Web3, contract, function_call):
    """Send a transaction to a specific Pi node."""
    nonce = w3.eth.get_transaction_count(sender_address)
    tx = function_call.build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': 0
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"Tx sent to {w3.provider.endpoint_uri}: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        print("Transaction failed.")
        try:
            tx_call = {
                'to': tx['to'],
                'from': sender_address,
                'data': tx['data'],
                'gas': tx['gas']
            }
            w3.eth.call(tx_call, block_identifier=receipt.blockNumber)
        except ContractLogicError as e:
            print(f"Revert reason: {e}")
        except Exception as e:
            print(f"Error decoding revert reason: {e}")

    return receipt


def get_contract(w3: Web3):
    """Return the contract instance."""
    return w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

# ============================================================
#                 API ROUTES
# ============================================================

@app.get('/')
def health_check():
    return {"health": "ok", "status": True, "version": "2.0.0", "mode": "hostname-routing"}


@app.get('/contract')
def get_contract_info():
    return {"contractAddress": CONTRACT_ADDRESS, "status": True}


@app.get('/private-key')
def get_private_key_info():
    return {"Private Key": PRIVATE_KEY, "status": True}


@app.post("/register")
async def register_participant(hostname: str):
    if hostname not in pi_semaphores:
        raise HTTPException(status_code=404, detail=f"No Pi found for hostname {hostname}")

    sem = pi_semaphores[hostname]
    async with sem:
        w3 = get_web3_for_pi(hostname)
        contract = get_contract(w3)
        receipt = send_transaction(w3, contract, contract.functions.register())

        if receipt.status == 1:
            return {"status": "success", "hostname": hostname}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed.")


@app.post("/submit-data")
async def submit_data(hostname: str, role: int, energy: int, price: int):
    if hostname not in pi_semaphores:
        raise HTTPException(status_code=404, detail=f"No Pi found for hostname {hostname}")

    sem = pi_semaphores[hostname]
    async with sem:
        w3 = get_web3_for_pi(hostname)
        contract = get_contract(w3)
        receipt = send_transaction(w3, contract, contract.functions.submitData(role, energy, price))

        if receipt.status == 1:
            return {"status": "success", "hostname": hostname}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed.")


@app.post("/advance-phase")
async def advance_phase(hostname: str):
    if hostname not in pi_semaphores:
        raise HTTPException(status_code=404, detail=f"No Pi found for hostname {hostname}")

    sem = pi_semaphores[hostname]
    async with sem:
        w3 = get_web3_for_pi(hostname)
        contract = get_contract(w3)
        receipt = send_transaction(w3, contract, contract.functions.advancePhase())

        if receipt.status == 1:
            return {"status": "success", "hostname": hostname}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed.")


@app.post("/submit-execution-result")
async def submit_execution_result(hostname: str):
    if hostname not in pi_semaphores:
        raise HTTPException(status_code=404, detail=f"No Pi found for hostname {hostname}")

    sem = pi_semaphores[hostname]
    async with sem:
        w3 = get_web3_for_pi(hostname)
        contract = get_contract(w3)
        result_hash_hex = run_matching_and_get_hash(contract)

        if not result_hash_hex:
            raise HTTPException(status_code=400, detail="No participants found or matching failed.")

        receipt = send_transaction(
            w3, contract, contract.functions.submitExecutionResult(Web3.to_bytes(hexstr=result_hash_hex))
        )

        if receipt.status == 1:
            return {"status": "success", "hostname": hostname}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed.")


@app.post("/verify-execution")
async def verify_execution(hostname: str):
    if hostname not in pi_semaphores:
        raise HTTPException(status_code=404, detail=f"No Pi found for hostname {hostname}")

    sem = pi_semaphores[hostname]
    async with sem:
        w3 = get_web3_for_pi(hostname)
        contract = get_contract(w3)
        receipt = send_transaction(w3, contract, contract.functions.verifyExecutionResult())

        if receipt.status == 1:
            return {"status": "success", "hostname": hostname}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed.")


# ============================================================
#                READ-ONLY QUERIES
# ============================================================

@app.get("/total-participants")
def total_participants(hostname: str):
    w3 = get_web3_for_pi(hostname)
    contract = get_contract(w3)
    value = contract.functions.TOTAL_PARTICIPANTS().call()
    return {"TOTAL_PARTICIPANTS": value, "hostname": hostname}


@app.get("/current-phase")
def get_current_phase(hostname: str):
    w3 = get_web3_for_pi(hostname)
    contract = get_contract(w3)
    phase = contract.functions.currentPhase().call()
    phase_mapping = {0: "DataSubmission", 1: "Execution", 2: "Verification"}
    return {"currentPhase": phase_mapping.get(phase, str(phase)), "hostname": hostname}


@app.get("/previous-hash")
def get_previous_hash(hostname: str):
    w3 = get_web3_for_pi(hostname)
    contract = get_contract(w3)
    phash = contract.functions.previousHash().call()
    return {"previousHash": phash.hex() if isinstance(phash, bytes) else phash, "hostname": hostname}


# ============================================================
#                 RUN SERVER
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_controller:app", host="0.0.0.0", port=8005, reload=True)
