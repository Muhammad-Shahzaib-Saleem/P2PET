#source ../../pi-venv/bin/activate
import subprocess
from eth_account import Account
import os, time
import json
from web3 import Web3
# from web3.middleware import geth_poa_middleware
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from web3.exceptions import ContractLogicError
import socket
from fastapi import FastAPI, HTTPException
import sys
from dotenv import load_dotenv
from fetch_and_match import run_matching_and_get_hash
from pathlib import Path
import paramiko
from fastapi.middleware.cors import CORSMiddleware
import requests

import time
import atexit
import threading
from contextlib import asynccontextmanager


from eth_utils import to_checksum_address

app = FastAPI()

MATCH_FILE = "matching_result.json"

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)

load_dotenv()


def load_matches():
    with open(MATCH_FILE) as f:
        return json.load(f)







PI_NODES = [
    {"name": "pi_1",  "host": "100.76.91.82",    "username": "pi", "password": "Lums12345", "port": 8001},
    {"name": "pi_2",  "host": "100.93.80.36",    "username": "pi", "password": "Lums12345", "port": 8002},
    {"name": "pi_15", "host": "100.120.124.29",  "username": "pi", "password": "Lums12345", "port": 8003},
]


PI_PROJECT_DIR  = "/home/pi/Desktop/P2PET_Dynamic/P2PET"
PI_VENV_ACTIVATE = f"source {PI_PROJECT_DIR}/venv/bin/activate"
PI_API_DIR       = f"{PI_PROJECT_DIR}/p2p-energy-trading-contract/api"

def start_pi(node: dict) -> bool:
    name, host, username, password, port = (
        node["name"], node["host"], node["username"], node["password"], node["port"]
    )
    print(f"[{name}] Connecting to {host} ...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"[{name}] ❌ SSH failed: {e}")
        return False

    # Kill any old instance on that port
    _, stdout, _ = client.exec_command(f"fuser -k {port}/tcp 2>/dev/null || true")
    stdout.channel.recv_exit_status()
    time.sleep(0.5)

    start_cmd = (
        f"cd {PI_API_DIR} && "
        f"{PI_VENV_ACTIVATE} && "
        f"nohup python meter_api.py --port {port} > meter_{port}.log 2>&1 &"
    )
    _, stdout, _ = client.exec_command(start_cmd)
    stdout.channel.recv_exit_status()
    time.sleep(3)

    _, stdout, _ = client.exec_command("pgrep -fa meter_api.py")
    running = bool(stdout.read().decode().strip())
    client.close()

    if running:
        print(f"[{name}] ✅  http://{host}:{port}")
    else:
        print(f"[{name}] ❌ Process did not start")
    return running

def start_all_pis():
    print("\n🚀 Starting meter_api.py on all Pi nodes...")
    for node in PI_NODES:
        start_pi(node)
    print("✅ Pi startup sequence complete.\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs once at startup — in background so API is immediately available
    thread = threading.Thread(target=start_all_pis, daemon=True)
    thread.start()
    yield
    # (optional teardown goes here)
# app
app = FastAPI(title="P2P Energy Trading API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify ["http://localhost:5173"] for stricter control
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.168.0.1', 80))
        return s.getsockname()[0]
    finally:
        s.close()

ip_address = get_local_ip()

with open("NodeNum.txt", "r") as f:
    node_number = int(f.read().strip())

rpc_port_num = 22000

import json

def get_pi_hostname(host, file_path='pis.json'):
    """
    Given a host name, return its hostname and user from pis.json.
    
    Args:
        host (str): The host key (e.g., "pi_1", "pi_4Ethernet").
        file_path (str): Path to the pis.json file.
    
    Returns:
        dict: A dictionary with 'hostname' and 'user' if found, else None.
    """
    try:
        with open(file_path, 'r') as f:
            pis = json.load(f)

        for pi in pis:
            if pi['host'] == host:
                return {"hostname": pi['hostname']}
        
        print(f"Host '{host}' not found in {file_path}")
        return None

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: '{file_path}' is not a valid JSON file.")
        return None




RPC_URL = f"http://{'100.76.91.82'}:{str(rpc_port_num+node_number)}"

# RPC_URL = f"https://100.110.53.19:22004"
# LOCAL_RPC_URL = "https://127.0.0.1:22000"
# LOCAL_PRIVATE_KEY = os.getenv("PRIVATE_KEY")

CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")
ABI_PATH = os.getenv("ABI_PATH")

# Keystore and contract details
keystore = subprocess.check_output(
    "cd ..; cd ..; cd quorum-ibft-chain; cd node*; cd data/keystore; cat $(ls | head -n 1)",
    shell=True,
    text=True,
).strip()

ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")
PI_PASSWORD = "Lums12345"


with open(CONTRACT_ADDRESS_PATH, "r") as f:
    data = json.load(f)
    CONTRACT_ADDRESS = data["contract_address"]


with open(ABI_PATH, "r") as abi_file:
    abi = json.load(abi_file)


try:
    private_key_bytes = Account.decrypt(keystore, ACCOUNT_PASSWORD)
    PRIVATE_KEY = private_key_bytes.hex()
except Exception as e:
    raise RuntimeError(f"Failed to decrypt private key: {e}")

# Web3 instance
# Web3 instance
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Set up account
account = w3.eth.account.from_key(PRIVATE_KEY)
sender_address = account.address

# Contract instance
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)





def get_dynamic_private_key(node_number, base_dir="/home/pi/Desktop/P2PET_Dynamic/P2PET/quorum-ibft-chain",
                             account_password=ACCOUNT_PASSWORD, remote_host=None, remote_user="pi", remote_password=PI_PASSWORD):
    """
    Decrypts and returns the private key for a given node number.
    Works locally or remotely (via SSH with password authentication).
    """
    try:
        node_path = Path(base_dir) / f"node{node_number}" / "data" / "keystore"

        # --- 🔹 Remote access using paramiko (no password prompt) ---
        if remote_host:
            print(f"🔄 Fetching keystore from remote Pi: {remote_host}")

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(remote_host, username=remote_user, password=remote_password)

            # Get keystore filename
            stdin, stdout, stderr = ssh.exec_command(f"ls {node_path} | head -n 1")
            keystore_filename = stdout.read().decode().strip()
            if not keystore_filename:
                raise FileNotFoundError(f"No keystore file found at {node_path}")

            # Read keystore content directly (no file saving)
            stdin, stdout, stderr = ssh.exec_command(f"cat {node_path}/{keystore_filename}")
            keystore_content = stdout.read().decode()
            ssh.close()

        # --- 🔹 Local mode ---
        else:
            keystore_files = list(node_path.glob("*"))
            if not keystore_files:
                raise FileNotFoundError(f"No keystore files found in {node_path}")
            with open(keystore_files[0], "r") as f:
                keystore_content = f.read()

        # --- 🔹 Decrypt private key ---
        private_key_bytes = Account.decrypt(keystore_content, account_password)
        private_key_hex = private_key_bytes.hex()
        print(f"✅ Successfully decrypted private key for node{node_number}")

        return private_key_hex

    except Exception as e:
        raise RuntimeError(f"Failed to get private key for node {node_number}: {e}")

dynamic_private_key=get_dynamic_private_key(0, remote_host="100.76.91.82")
print("Private Key",dynamic_private_key)



def get_web3_rpc(hostname, pis_json_path="pis.json"):
    """Creates a Web3 connection and contract instance dynamically using pis.json."""
    try:
        # Load pis.json
        with open(pis_json_path, "r") as f:
            pis_data = json.load(f)

        # Ensure hostname exists in pis.json
        if hostname not in pis_data:
            raise HTTPException(status_code=404, detail=f"Hostname {hostname} not found in pis.json")

        node_info = pis_data[hostname]
        node_number = node_info["node_num"]
        node_hostname = node_info["hostname"]

        # Build dynamic RPC URL
        RPC_URL = f"http://{node_hostname}:{rpc_port_num + node_number}"
        print(f"Connecting to RPC: {RPC_URL}")

        # Connect to Web3
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        if not w3.is_connected():
            raise Exception(f"Cannot connect to {RPC_URL}")


        # Get dynamic private key
        dynamic_private_key = get_dynamic_private_key(node_number, remote_host=node_hostname)  

        # Load sender account
        account = w3.eth.account.from_key(dynamic_private_key)
        sender_address = account.address

        # Load contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=abi
        )

        print(f"Connected successfully to node {node_number} ({hostname})")
        return w3, contract, sender_address,dynamic_private_key

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pis.json file not found")
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Missing key in pis.json: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing Web3: {e}")


def send_transaction(function_call):
    nonce = w3.eth.get_transaction_count(sender_address)

    tx = function_call.build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': 0
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

    # Use correct attribute name for Web3.py v6+
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"Transaction sent: {tx_hash.hex()} — waiting for receipt...")
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
            revert_msg = w3.eth.call(tx_call, block_identifier=receipt.blockNumber)
            print("Unknown failure reason.")
        except ContractLogicError as e:
            message = str(e)
            if message.startswith("execution reverted:"):
                clean_msg = message.split("execution reverted:")[1].strip()
                print(f"Revert reason: {clean_msg}")
            else:
                print(f"Revert reason: {message}")
        except Exception as e:
            print(f"Failed to decode revert reason: {e}")

    return receipt



def send_transaction_dynamic(w3, sender_address, function_call, dynamic_private_key):
    """Sends a transaction to the blockchain and returns receipt + revert reason if failed."""
    revert_reason = None
    try:
        nonce = w3.eth.get_transaction_count(sender_address)

        tx = function_call.build_transaction({
            'from': sender_address,
            'nonce': nonce,
            'gas': 500000,
            'gasPrice': 0
        })

        signed_tx = w3.eth.account.sign_transaction(tx, dynamic_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"Transaction sent: {tx_hash.hex()} — waiting for receipt...")
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
                # Try to trigger the revert reason by simulating the call
                w3.eth.call(tx_call, block_identifier=receipt.blockNumber)
            except ContractLogicError as e:
                message = str(e)
                if message.startswith("execution reverted:"):
                    revert_reason = message.split("execution reverted:")[1].strip()
                    print(f"Revert reason: {revert_reason}")
                else:
                    revert_reason = message
                    print(f"Revert reason: {revert_reason}")
            except Exception as e:
                revert_reason = f"Failed to decode revert reason: {e}"
                print(revert_reason)

        return receipt, revert_reason

    except Exception as e:
        print(f"Error sending transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending transaction: {e}")



@app.get('/')
def checking_contract():
    try:
        return {"health":"ok","status": True,"version":"2.0.0","description":"This is P2P Energy trading contract api (Endoints)"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

print("Contract Address:",CONTRACT_ADDRESS)
@app.get('/contract')
def checking_contract():
    try:
        return {"contractAddress": CONTRACT_ADDRESS,"status": True}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/private-key')
def checking_contract():
    try:
        return {"Private Keys": PRIVATE_KEY,"status": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/dynamic_private-key/{hostname}')
def dynamic_key(hostname: str):
    try:
        _, _, _, dynamic_private_key = get_web3_rpc(hostname)
        return {"Dynamic Private Key": dynamic_private_key, "status": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/dynamic_register")
def register_participant(hostname: str):
    """Registers participant dynamically based on Pi hostname."""
    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        function_call = contract.functions.register()

        receipt, revert_reason = send_transaction_dynamic(w3, sender_address, function_call, dynamic_private_key)

        if receipt.status == 1:
            return {"status": "success", "txHash": receipt.transactionHash.hex()}
        else:
            reason = revert_reason or "Transaction reverted or failed."
            raise HTTPException(status_code=400, detail={"status": "failed", "reason": reason})

    except HTTPException:
        raise  # re-raise our controlled exceptions
    except Exception as e:
        revert_reason = str(e)
        if "execution reverted" in revert_reason:
            start = revert_reason.find("execution reverted")
            revert_reason = revert_reason[start:]
        raise HTTPException(
            status_code=400,
            detail={"status": "failed", "reason": revert_reason}
        )




@app.post("/register")
def register_participant():
    receipt = send_transaction(contract.functions.register())
    if receipt.status == 1:
        return {"status": "success", "message": "Transaction successful."}
    else:
        raise HTTPException(status_code=400, detail="Transaction failed.")


@app.post("/submit-data")
def submit_data(role:int, energy:int, price:int):
    receipt = send_transaction(contract.functions.submitData(role, energy, price))
    if receipt.status == 1:
        return {"status": "success", "message": "Transaction successful."}
    else:
        raise HTTPException(status_code=400, detail="Transaction failed.")


ROLE_MAP = {
    "buyer": 1,
    "seller": 2
}

SCALING_FACTOR = 100

def scale(value):
    return int(value * SCALING_FACTOR)

@app.post("/dynamic_submit_data")
def submit_data(hostname: str, role: str, energy: int, price: int):
    """Submits participant data dynamically and returns success or revert reason."""
    role_normalized = role.strip().lower()
    if role_normalized not in ROLE_MAP:
        raise HTTPException(status_code=400, detail="Invalid role")

    role_int = ROLE_MAP[role_normalized]
    energy_scaled = scale(energy)
    price_scaled = scale(price)

    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        function_call = contract.functions.submitData(role_int, energy_scaled, price_scaled)

        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, function_call, dynamic_private_key
        )

        if receipt.status == 1:
            return {
                "status": "success",
                "message": "Transaction successful.",
                "txHash": receipt.transactionHash.hex(),
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "failed",
                    "reason": revert_reason or "Transaction reverted or failed.",
                    "txHash": receipt.transactionHash.hex() if receipt else None,
                },
            )

    except HTTPException:
        # Pass through known errors
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Unexpected error occurred: {str(e)}",
            },
        )
    raise HTTPException(status_code=400, detail="Transaction failed.")





@app.post("/Dynamic_hash_participants")
def hash_participants(hostname: str):
    try:
        # 🔹 Step 1: Get web3, contract, sender, and private key
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)

        # 🔹 Step 2: Prepare function call
        function_call = contract.functions.hashParticipantsList()

        # 🔹 Step 3: Send transaction using dynamic signing function
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, function_call, dynamic_private_key
        )

        # 🔹 Step 4: Fetch the latest computed hash from contract state
        latest_hash = contract.functions.previousHash().call()

        # 🔹 Step 5: Handle transaction result
        if receipt.status == 1:
            tx_hash = receipt.transactionHash.hex()
            return {
                "status": "success",
                "message": "✅ Hash calculated and submitted successfully.",
                "computedHash": latest_hash.hex(),
                "txHash": tx_hash
            }
        else:
            reason = revert_reason or "Transaction failed without revert reason."
            raise HTTPException(status_code=400, detail={"reason": reason})

    except HTTPException:
        # rethrow HTTP exceptions cleanly
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")




PHASE_NAMES = {
    0: "DataSubmission",
    1: "Execution",
    2: "Trading"
}



@app.post("/dynamic_advance_phase")
def advance_phase(hostname: str):
    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        function_call = contract.functions.advancePhase()

        # Send transaction using dynamic private key
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, function_call, dynamic_private_key
        )

         # Replace if using another network

        # Fetch current phase and round
        current_phase = contract.functions.currentPhase().call()
        current_round = contract.functions.currentRound().call()
        phase_name = PHASE_NAMES.get(current_phase, f"Unknown({current_phase})")

        if receipt.status == 1:
            return {
                "status": "success",
                "message": "Phase advanced successfully.",
                "currentRound": current_round,
                "phaseName": phase_name,
                "txHash": receipt.transactionHash.hex(),
                "revert_reason": revert_reason
            }
        else:
            return {
                "status": "failed",
                "message": "Transaction failed.",
                "currentRound": current_round,
                "phaseName": phase_name,
                "txHash": receipt.transactionHash.hex(),
                "revert_reason": revert_reason or "Transaction failed without revert reason"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/dynamic_submit_execution_result")
def dynamic_submit_execution_result(hostname: str):
    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        participant_count, result_hash_hex = run_matching_and_get_hash(contract)

        # Build bytes32-compatible hash
        hash_bytes32 = Web3.to_bytes(hexstr="0x" + result_hash_hex)

        function_call = contract.functions.submitExecutionResult(hash_bytes32)
        print("Participant Count:", participant_count)
        # Send transaction using the dynamic private key method
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, function_call, dynamic_private_key
        )

        explorer_url = f"https://etherscan.io/tx/{receipt.transactionHash.hex()}"  # Replace with proper chain explorer if needed

        if receipt.status == 1:
            return {
                "status": "success",
                "participants": participant_count,
                "result_hash": f"0x{result_hash_hex}",
                "txHash": receipt.transactionHash.hex(),
                "explorerUrl": explorer_url,
                "revert_reason": revert_reason
            }
        else:
            return {
                "status": "failed",
                "participants": participant_count,
                "result_hash": f"0x{result_hash_hex}",
                "txHash": receipt.transactionHash.hex(),
                "explorerUrl": explorer_url,
                "revert_reason": revert_reason or "Transaction failed without revert reason"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))








@app.post("/verify_execution")
def verify_execution():
    receipt = send_transaction(contract.functions.verifyExecutionResult())
    if receipt.status == 1:
        return {"status": "success", "message": "Transaction successful."}
    else:
        raise HTTPException(status_code=400, detail="Transaction failed.")
    






@app.post("/dynamic_verify_execution")
def dynamic_verify_execution(hostname: str):
    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        # Get return values using a call (doesn't change state)
        majority_hash, is_verified = contract.functions.verifyExecutionResult().call({'from': sender_address})
        function_call = contract.functions.verifyExecutionResult()

        # Send transaction dynamically
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, function_call, dynamic_private_key
        )

 
        if receipt.status == 1:
            return {
                "status": "success",
                "message": "Execution verified successfully.",
                "txHash": receipt.transactionHash.hex(),
                "majority_hash": majority_hash.hex(),  # convert bytes32 to hex
                "is_verified": is_verified,
                "revert_reason": revert_reason
            }
        else:
            return {
                "status": "failed",
                "message": "Transaction failed.",
                "txHash": receipt.transactionHash.hex(),
                
                "revert_reason": revert_reason or "Transaction failed without revert reason"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/total_participants")
def get_total_participants():
    try:
        value = contract.functions.TOTAL_PARTICIPANTS().call()
        return {"TOTAL_PARTICIPANTS": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/participants_list")
def get_participants_list():
    try:
        total = contract.functions.TOTAL_PARTICIPANTS().call()
        participants = []
        for i in range(1,total):
            data = contract.functions.participantsList(i).call()
            participants.append(data)
        return {"participantsList": participants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/address_to_slot/{address}")
def get_address_to_slot(address: str):
    try:
        checksum_addr = Web3.to_checksum_address(address)
        slot = contract.functions.addressToSlot(checksum_addr).call()
        return {"address": checksum_addr, "slot": slot}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/next_available_slot")
def get_next_available_slot():
    try:
        slot = contract.functions.nextAvailableSlot().call()
        return {"nextAvailableSlot": slot}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current_round")
def get_current_round():
    try:
        round_num = contract.functions.currentRound().call()
        return {"currentRound": round_num}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current_phase")
def get_current_phase():
    try:
        phase = contract.functions.currentPhase().call()
        phase_mapping = {
            0: "DataSubmission",
            1: "Execution",
            2: "Verification",
            # add more if needed
        }
        phase_str = phase_mapping.get(phase, str(phase))
        return {"currentPhase": phase_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/previous_hash")
def get_previous_hash():
    try:
        phash = contract.functions.previousHash().call()
        return {"previousHash": phash.hex() if isinstance(phash, bytes) else phash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/previous_hash_execution")
def get_previous_hash_execution():
    try:
        phash_exec = contract.functions.previousHashExecution().call()
        return {"previousHashExecution": phash_exec.hex() if isinstance(phash_exec, bytes) else phash_exec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/final_hash")
def get_final_hash():
    try:
        fhash = contract.functions.finalHash().call()
        return {"finalHash": fhash.hex() if isinstance(fhash, bytes) else fhash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/submitted_results")
def get_submitted_results():
    try:
        results = []
        for i in range(5):
            submitter, result_hash = contract.functions.submittedResults(i).call()
            results.append({
                "submitter": submitter,
                "resultHash": result_hash.hex()  # convert bytes32 → hex string
            })
        return {"submittedResults": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result_submission_count")
def get_result_submission_count():
    try:
        count = contract.functions.resultSubmissionCount().call()
        return {"resultSubmissionCount": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/has_submitted_result/{address}")
def get_has_submitted_result(address: str):
    try:
        checksum_addr = Web3.to_checksum_address(address)
        has_submitted = contract.functions.hasSubmittedResult(checksum_addr).call()
        return {"address": checksum_addr, "hasSubmittedResult": has_submitted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# -----------------------------Controling Hardware and Relaying  -----------------------------------


def get_eth_address_from_ip(ip: str):
    hostname = ip
    if not hostname:
        raise Exception("Hostname not found")

    w3, _, sender_address, _ = get_web3_rpc(hostname)
    return sender_address


@app.get("/pi/address-from-ip/{ip}")
def address_from_ip(ip: str):
    try:
        address = get_eth_address_from_ip(ip)
        return {
            "ip": ip,
            "eth_address": address
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# @app.post("/energy/transfer/start")
# def start_transfer(ip: str):
#     my_addr = get_eth_address_from_ip(ip).lower()
#     matches = load_matches()

#     my_matches = [
#         m for m in matches
#         if m["buyer_id"].lower() == my_addr
#         or m["seller_id"].lower() == my_addr
#     ]

#     if not my_matches:
#         raise HTTPException(404, "No matching energy found")

#     results = []

#     for m in my_matches:
#         target = m["energy_matched"]

#         # ---------------- BUYER ----------------
#         if m["buyer_id"].lower() == my_addr:
#             start = read_import_energy()
#             if start is None:
#                 raise HTTPException(500, "Meter read failed")

#             relay_on()

#             while True:
#                 now = read_import_energy()
#                 if now and (now - start) >= target:
#                     relay_off()
#                     break
#                 time.sleep(1)

#             results.append({
#                 "role": "buyer",
#                 "energy_received": round(now - start, 3)
#             })

#         # ---------------- SELLER ----------------
#         if m["seller_id"].lower() == my_addr:
#             start = read_export_energy()
#             if start is None:
#                 raise HTTPException(500, "Meter read failed")

#             relay_on()

#             while True:
#                 now = read_export_energy()
#                 if now and (now - start) >= target:
#                     relay_off()
#                     break
#                 time.sleep(1)

#             results.append({
#                 "role": "seller",
#                 "energy_sent": round(now - start, 3)
#             })

#     return {
#         "eth_address": my_addr,
#         "status": "completed",
#         "details": results
#     }



if __name__ == "__main__":
    
    import uvicorn
    import webbrowser

    local_ip = get_local_ip()
    print("\n🚀 P2P Energy Trading API running!")
    print(f"   → Local Access:   http://localhost:8000")
    print(f"   → Network Access: http://{local_ip}:8000\n")

    # Optional: open in browser (comment out if not desired)
    # webbrowser.open(f"http://{local_ip}:8000")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # allows both localhost and network access
        port=8000,
        reload=True
    )