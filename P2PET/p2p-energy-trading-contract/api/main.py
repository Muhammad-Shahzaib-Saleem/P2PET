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
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai


load_dotenv()

# ==================== CHATBOT CONFIGURATION ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCm3P9l_xvfiSHCt-lH3GFE_rZCf4hulr4")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Chat message model
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    
# Load pis.json for chatbot
def load_pis_config():
    try:
        with open("pis.json", "r") as f:
            pis = json.load(f)
            return {pi_data["host"]: pi_data for pi_data in pis.values()}
    except:
        return {}

# app
app = FastAPI(title="P2P Energy Trading API")

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

# with open("NodeNum.txt", "r") as f:
#     node_number = int(f.read().strip())

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




RPC_URL = f"http://{'100.93.80.36'}:{str(rpc_port_num)}"

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

dynamic_private_key=get_dynamic_private_key(0, remote_host="100.93.80.36")
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


# ==================== CHATBOT ENDPOINT ====================

# Define tools for Gemini function calling
CHATBOT_TOOLS = [
    {
        "name": "get_available_pis",
        "description": "Get list of all available Raspberry Pi nodes that can be used for blockchain operations. Returns hostnames like pi_2, pi_4, etc.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "register_participant",
        "description": "Register a Raspberry Pi as a participant on the blockchain for P2P energy trading. Must be done before submitting trades.",
        "parameters": {
            "type": "object",
            "properties": {
                "hostname": {"type": "string", "description": "Pi hostname from available pis (e.g., 'pi_2', 'pi_4', 'pi_11', 'pi_14')"}
            },
            "required": ["hostname"]
        }
    },
    {
        "name": "submit_trade",
        "description": "Submit a bid (buyer) or offer (seller) for energy trading. Must be in DataSubmission phase.",
        "parameters": {
            "type": "object",
            "properties": {
                "hostname": {"type": "string", "description": "Pi hostname"},
                "role": {"type": "string", "enum": ["buyer", "seller"], "description": "Trading role"},
                "energy": {"type": "integer", "description": "Amount of energy in kWh"},
                "price": {"type": "integer", "description": "Price per kWh"}
            },
            "required": ["hostname", "role", "energy", "price"]
        }
    },
    {
        "name": "get_participants",
        "description": "Get list of all registered participants on the blockchain",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_total_participants",
        "description": "Get total count of registered participants",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_current_phase",
        "description": "Get current trading phase. Phases: 0=DataSubmission, 1=Execution, 2=Trading",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_current_round",
        "description": "Get current trading round number",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "advance_phase",
        "description": "Advance to next phase in the trading round. DataSubmission→Execution→Trading→DataSubmission",
        "parameters": {
            "type": "object",
            "properties": {
                "hostname": {"type": "string", "description": "Pi hostname to trigger the phase advance"}
            },
            "required": ["hostname"]
        }
    },
    {
        "name": "hash_participants",
        "description": "Calculate and store hash of current participants' submitted data. Called at end of DataSubmission phase.",
        "parameters": {
            "type": "object",
            "properties": {
                "hostname": {"type": "string", "description": "Pi hostname to trigger hash calculation"}
            },
            "required": ["hostname"]
        }
    },
    {
        "name": "submit_execution_result",
        "description": "Submit execution result after running the double auction algorithm. Called during Execution phase.",
        "parameters": {
            "type": "object",
            "properties": {
                "hostname": {"type": "string", "description": "Pi hostname to submit execution result"}
            },
            "required": ["hostname"]
        }
    },
    {
        "name": "verify_execution",
        "description": "Verify the execution result by comparing submitted hashes from different nodes.",
        "parameters": {
            "type": "object",
            "properties": {
                "hostname": {"type": "string", "description": "Pi hostname to verify execution"}
            },
            "required": ["hostname"]
        }
    },
    {
        "name": "get_contract_address",
        "description": "Get the deployed smart contract address on the blockchain",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
]


def execute_chatbot_function(name: str, args: dict) -> dict:
    """Execute a chatbot function and return the result"""
    try:
        if name == "get_available_pis":
            pis = load_pis_config()
            return {
                "status": "success",
                "total": len(pis),
                "pis": [{"host": h, "ip": info["hostname"], "node_num": info["node_num"]} for h, info in pis.items()]
            }
        
        elif name == "register_participant":
            hostname = args.get("hostname")
            # Call the existing endpoint logic
            try:
                w3_inst, contract_inst, sender_addr, dyn_key = get_web3_rpc(hostname)
                function_call = contract_inst.functions.register()
                receipt, revert_reason = send_transaction_dynamic(w3_inst, sender_addr, function_call, dyn_key)
                if receipt.status == 1:
                    return {"status": "success", "txHash": receipt.transactionHash.hex(), "message": f"Successfully registered {hostname}"}
                else:
                    return {"status": "failed", "reason": revert_reason or "Transaction failed"}
            except Exception as e:
                error_msg = str(e)
                if "already registered" in error_msg.lower():
                    return {"status": "info", "message": f"{hostname} is already registered as a participant"}
                return {"status": "error", "message": error_msg}
        
        elif name == "submit_trade":
            hostname = args.get("hostname")
            role = args.get("role")
            energy = args.get("energy")
            price = args.get("price")
            
            role_map = {"buyer": 1, "seller": 2}
            if role.lower() not in role_map:
                return {"status": "error", "message": "Invalid role. Must be 'buyer' or 'seller'"}
            
            try:
                w3_inst, contract_inst, sender_addr, dyn_key = get_web3_rpc(hostname)
                function_call = contract_inst.functions.submitData(role_map[role.lower()], energy * 100, price * 100)
                receipt, revert_reason = send_transaction_dynamic(w3_inst, sender_addr, function_call, dyn_key)
                if receipt.status == 1:
                    return {"status": "success", "txHash": receipt.transactionHash.hex(), 
                            "message": f"Submitted {role} order: {energy} kWh @ {price}/kWh from {hostname}"}
                else:
                    return {"status": "failed", "reason": revert_reason or "Transaction failed"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif name == "get_participants":
            total = contract.functions.TOTAL_PARTICIPANTS().call()
            participants = []
            for i in range(1, total):
                addr = contract.functions.participantsList(i).call()
                if addr != "0x0000000000000000000000000000000000000000":
                    participants.append(addr)
            return {"status": "success", "participants": participants, "count": len(participants)}
        
        elif name == "get_total_participants":
            value = contract.functions.TOTAL_PARTICIPANTS().call()
            return {"status": "success", "total_participants": value}
        
        elif name == "get_current_phase":
            phase = contract.functions.currentPhase().call()
            phase_names = {0: "DataSubmission", 1: "Execution", 2: "Trading"}
            return {"status": "success", "phase": phase, "phase_name": phase_names.get(phase, f"Unknown({phase})")}
        
        elif name == "get_current_round":
            round_num = contract.functions.currentRound().call()
            return {"status": "success", "current_round": round_num}
        
        elif name == "advance_phase":
            hostname = args.get("hostname")
            try:
                w3_inst, contract_inst, sender_addr, dyn_key = get_web3_rpc(hostname)
                function_call = contract_inst.functions.advancePhase()
                receipt, revert_reason = send_transaction_dynamic(w3_inst, sender_addr, function_call, dyn_key)
                
                current_phase = contract_inst.functions.currentPhase().call()
                current_round = contract_inst.functions.currentRound().call()
                phase_names = {0: "DataSubmission", 1: "Execution", 2: "Trading"}
                
                if receipt.status == 1:
                    return {"status": "success", "txHash": receipt.transactionHash.hex(),
                            "new_phase": phase_names.get(current_phase, str(current_phase)),
                            "current_round": current_round}
                else:
                    return {"status": "failed", "reason": revert_reason or "Transaction failed"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif name == "hash_participants":
            hostname = args.get("hostname")
            try:
                w3_inst, contract_inst, sender_addr, dyn_key = get_web3_rpc(hostname)
                function_call = contract_inst.functions.hashParticipantsList()
                receipt, revert_reason = send_transaction_dynamic(w3_inst, sender_addr, function_call, dyn_key)
                
                if receipt.status == 1:
                    latest_hash = contract_inst.functions.previousHash().call()
                    return {"status": "success", "txHash": receipt.transactionHash.hex(),
                            "computed_hash": latest_hash.hex()}
                else:
                    return {"status": "failed", "reason": revert_reason or "Transaction failed"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif name == "submit_execution_result":
            hostname = args.get("hostname")
            try:
                w3_inst, contract_inst, sender_addr, dyn_key = get_web3_rpc(hostname)
                participant_count, result_hash_hex = run_matching_and_get_hash(contract_inst)
                hash_bytes32 = Web3.to_bytes(hexstr="0x" + result_hash_hex)
                function_call = contract_inst.functions.submitExecutionResult(hash_bytes32)
                receipt, revert_reason = send_transaction_dynamic(w3_inst, sender_addr, function_call, dyn_key)
                
                if receipt.status == 1:
                    return {"status": "success", "txHash": receipt.transactionHash.hex(),
                            "participants": participant_count, "result_hash": f"0x{result_hash_hex}"}
                else:
                    return {"status": "failed", "reason": revert_reason or "Transaction failed"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif name == "verify_execution":
            hostname = args.get("hostname")
            try:
                w3_inst, contract_inst, sender_addr, dyn_key = get_web3_rpc(hostname)
                majority_hash, is_verified = contract_inst.functions.verifyExecutionResult().call({'from': sender_addr})
                function_call = contract_inst.functions.verifyExecutionResult()
                receipt, revert_reason = send_transaction_dynamic(w3_inst, sender_addr, function_call, dyn_key)
                
                if receipt.status == 1:
                    return {"status": "success", "txHash": receipt.transactionHash.hex(),
                            "majority_hash": majority_hash.hex(), "is_verified": is_verified}
                else:
                    return {"status": "failed", "reason": revert_reason or "Transaction failed"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif name == "get_contract_address":
            return {"status": "success", "contract_address": CONTRACT_ADDRESS}
        
        else:
            return {"status": "error", "message": f"Unknown function: {name}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """AI Chatbot endpoint using Gemini with function calling"""
    
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured. Add it to your .env file.")
    
    try:
        # Convert tools to Gemini format
        gemini_tools = []
        for tool in CHATBOT_TOOLS:
            gemini_tools.append({
                "function_declarations": [{
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }]
            })
        
        # Create model with tools
        model = genai.GenerativeModel(
            model_name="gemini-pro-latest",
            tools=gemini_tools,
            system_instruction="""You are a helpful AI assistant for the P2P Energy Trading blockchain system.
            
You help users:
- Register Raspberry Pi nodes as participants
- Submit buy/sell orders for energy trading
- Check trading status (phase, round, participants)
- Advance through trading phases
- Monitor blockchain state

Available Pi nodes are: pi_2, pi_4, pi_11, pi_14

Trading phases:
1. DataSubmission (phase 0): Register participants and submit bids/offers
2. Execution (phase 1): Run matching algorithm and submit results
3. Trading (phase 2): Physical energy trading occurs

Always be helpful and explain what actions you're taking. If an operation fails, explain why and suggest solutions."""
        )
        
        # Build chat history for Gemini
        chat = model.start_chat(history=[])
        
        # Get the last user message
        user_message = request.messages[-1].content if request.messages else ""
        
        # Send message and handle function calls
        response = chat.send_message(user_message)
        
        # Check if Gemini wants to call a function
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Check for function calls in response
            function_calls = []
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
            
            if not function_calls:
                # No more function calls, extract text response
                break
            
            # Execute function calls
            function_responses = []
            for fc in function_calls:
                func_name = fc.name
                func_args = dict(fc.args) if fc.args else {}
                
                print(f"Executing function: {func_name} with args: {func_args}")
                result = execute_chatbot_function(func_name, func_args)
                print(f"Function result: {result}")
                
                function_responses.append({
                    "name": func_name,
                    "response": result
                })
            
            # Send function results back to Gemini
            response = chat.send_message([
                genai.protos.Part(function_response=genai.protos.FunctionResponse(
                    name=fr["name"],
                    response={"result": fr["response"]}
                )) for fr in function_responses
            ])
        
        # Extract final text response
        final_response = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    final_response += part.text
        
        return {
            "response": final_response or "I processed your request but couldn't generate a response.",
            "status": "success"
        }
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/chat/health")
def chat_health():
    """Check if chatbot is configured"""
    return {
        "status": "ok" if GEMINI_API_KEY else "not_configured",
        "message": "Chatbot ready" if GEMINI_API_KEY else "GEMINI_API_KEY not set in .env"
    }


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