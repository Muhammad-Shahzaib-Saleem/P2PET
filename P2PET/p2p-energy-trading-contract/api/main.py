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

load_dotenv()

# app
app = FastAPI(title="P2P Enerygy Trading API")

# Get local IP address and build RPC_URL properly
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('192.168.0.1', 1))
    ip_address = s.getsockname()[0]
finally:
    s.close()

RPC_URL = f"http://{ip_address}:22000"
LOCAL_RPC_URL = "http://127.0.0.1:22000"
LOCAL_PRIVATE_KEY = os.getenv("PRIVATE_KEY")

CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")
ABI_PATH = os.getenv("ABI_PATH")

# Keystore and contract details
keystore = subprocess.check_output(
    "cd ..; cd ..; cd quorum-ibft-chain; cd node*; cd data/keystore; cat $(ls | head -n 1)",
    shell=True,
    text=True,
).strip()

ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")


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
w3 = Web3(Web3.HTTPProvider(LOCAL_RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Set up account
account = w3.eth.account.from_key(PRIVATE_KEY)
sender_address = account.address

# Contract instance
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)


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


@app.post("/advance-phase")
def advance_phase():
    receipt = send_transaction(contract.functions.advancePhase())
    if receipt.status == 1:
        return {"status": "success", "message": "Transaction successful."}
    else:
        raise HTTPException(status_code=400, detail="Transaction failed.")


@app.post("/submit-execution-result")
def submit_execution_result(result: str):
    receipt = send_transaction(contract.functions.submitExecutionResult(Web3.keccak(text=result)))
    if receipt.status == 1:
        return {"status": "success", "message": "Transaction successful."}
    else:
        raise HTTPException(status_code=400, detail="Transaction failed.")


@app.post("/verify-execution")
def verify_execution():
    receipt = send_transaction(contract.functions.verifyExecutionResult())
    if receipt.status == 1:
        return {"status": "success", "message": "Transaction successful."}
    else:
        raise HTTPException(status_code=400, detail="Transaction failed.")


@app.get("/total-participants")
def get_total_participants():
    try:
        value = contract.functions.TOTAL_PARTICIPANTS().call()
        return {"TOTAL_PARTICIPANTS": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/participants-list")
def get_participants_list():
    try:
        total = contract.functions.TOTAL_PARTICIPANTS().call()
        participants = []
        for i in range(total):
            data = contract.functions.participantsList(i).call()
            participants.append(data)
        return {"participantsList": participants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/address-to-slot/{address}")
def get_address_to_slot(address: str):
    try:
        checksum_addr = Web3.to_checksum_address(address)
        slot = contract.functions.addressToSlot(checksum_addr).call()
        return {"address": checksum_addr, "slot": slot}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/next-available-slot")
def get_next_available_slot():
    try:
        slot = contract.functions.nextAvailableSlot().call()
        return {"nextAvailableSlot": slot}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current-round")
def get_current_round():
    try:
        round_num = contract.functions.currentRound().call()
        return {"currentRound": round_num}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current-phase")
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


@app.get("/previous-hash")
def get_previous_hash():
    try:
        phash = contract.functions.previousHash().call()
        return {"previousHash": phash.hex() if isinstance(phash, bytes) else phash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/previous-hash-execution")
def get_previous_hash_execution():
    try:
        phash_exec = contract.functions.previousHashExecution().call()
        return {"previousHashExecution": phash_exec.hex() if isinstance(phash_exec, bytes) else phash_exec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/final-hash")
def get_final_hash():
    try:
        fhash = contract.functions.finalHash().call()
        return {"finalHash": fhash.hex() if isinstance(fhash, bytes) else fhash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/submitted-results")
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



@app.get("/result-submission-count")
def get_result_submission_count():
    try:
        count = contract.functions.resultSubmissionCount().call()
        return {"resultSubmissionCount": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/has-submitted-result/{address}")
def get_has_submitted_result(address: str):
    try:
        checksum_addr = Web3.to_checksum_address(address)
        has_submitted = contract.functions.hasSubmittedResult(checksum_addr).call()
        return {"address": checksum_addr, "hasSubmittedResult": has_submitted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)