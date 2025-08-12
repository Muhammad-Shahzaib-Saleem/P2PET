from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
# from web3.middleware import geth_poa_middleware
from eth_account import Account
from hexbytes import HexBytes


load_dotenv()

ABI_PATH = "../compiled/EnergyTrade_abi.json"
CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")

WEB3_PROVIDER = "http://127.0.0.1:22000"
# CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

with open(CONTRACT_ADDRESS_PATH, "r") as f:
    data = json.load(f)
    CONTRACT_ADDRESS = data["contract_address"]


with open(ABI_PATH, "r") as abi_file:
    ABI = json.load(abi_file)

if not (WEB3_PROVIDER and CONTRACT_ADDRESS and PRIVATE_KEY):
    raise RuntimeError("Please set WEB3_PROVIDER, CONTRACT_ADDRESS and PRIVATE_KEY in .env")

w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
# If using a POA testnet (like BSC testnet or some Quorum setups) uncomment:
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

acct = Account.from_key(PRIVATE_KEY)
ADDRESS = acct.address

app = FastAPI(title="EnergyTrade API")

# # Minimal ABI subset for contract interactions (only the functions we need)
# ABI = [
#     # register()
#     {
#         "inputs": [],
#         "name": "register",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     # submitData(Role,uint256,uint256)
#     {
#         "inputs": [
#             {"internalType": "uint8", "name": "_role", "type": "uint8"},
#             {"internalType": "uint256", "name": "_energyAmount", "type": "uint256"},
#             {"internalType": "uint256", "name": "_pricePerKWh", "type": "uint256"}
#         ],
#         "name": "submitData",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     # advancePhase()
#     {
#         "inputs": [],
#         "name": "advancePhase",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     # hashParticipantsList()
#     {
#         "inputs": [],
#         "name": "hashParticipantsList",
#         "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     # submitExecutionResult(bytes32)
#     {
#         "inputs": [{"internalType": "bytes32", "name": "resultHash", "type": "bytes32"}],
#         "name": "submitExecutionResult",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     # verifyExecutionResult()
#     {
#         "inputs": [],
#         "name": "verifyExecutionResult",
#         "outputs": [
#             {"internalType": "bytes32", "name": "majorityHash", "type": "bytes32"},
#             {"internalType": "bool", "name": "isVerified", "type": "bool"}
#         ],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     # participantsList(uint256) getter
#     {
#         "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
#         "name": "participantsList",
#         "outputs": [
#             {"internalType": "address", "name": "id", "type": "address"},
#             {"internalType": "uint8", "name": "role", "type": "uint8"},
#             {"internalType": "uint256", "name": "energyAmount", "type": "uint256"},
#             {"internalType": "uint256", "name": "pricePerKWh", "type": "uint256"}
#         ],
#         "stateMutability": "view",
#         "type": "function"
#     },
#     # submittedResults(uint256) getter
#     {
#         "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
#         "name": "submittedResults",
#         "outputs": [
#             {"internalType": "address", "name": "submitter", "type": "address"},
#             {"internalType": "bytes32", "name": "resultHash", "type": "bytes32"}
#         ],
#         "stateMutability": "view",
#         "type": "function"
#     },
#     # currentPhase()
#     {
#         "inputs": [],
#         "name": "currentPhase",
#         "outputs": [{"internalType": "enum EnergyTrade.Phase", "name": "", "type": "uint8"}],
#         "stateMutability": "view",
#         "type": "function"
#     },
#     # currentRound()
#     {
#         "inputs": [],
#         "name": "currentRound",
#         "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
#         "stateMutability": "view",
#         "type": "function"
#     },
#     # TOTAL_PARTICIPANTS()
#     {
#         "inputs": [],
#         "name": "TOTAL_PARTICIPANTS",
#         "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
#         "stateMutability": "view",
#         "type": "function"
#     },
#     # finalHash()
#     {
#         "inputs": [],
#         "name": "finalHash",
#         "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
#         "stateMutability": "view",
#         "type": "function"
#     }
# ]


contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ABI)

# Helper: build, sign and send tx
def send_transaction(function_tx):
    """function_tx is contract.functions.<method>(...).buildTransaction(tx) OR the contract function itself"""
    # Build tx if not built already
    nonce = w3.eth.get_transaction_count(ADDRESS)
    tx = function_tx.buildTransaction({
        "from": ADDRESS,
        "nonce": nonce,
        "gas": 3000000,
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id
    })
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

# Pydantic models
class SubmitDataModel(BaseModel):
    role: int  # 0 = N_A, 1 = Buyer, 2 = Seller (enum from contract)
    energyAmount: int
    pricePerKWh: int

class SubmitExecutionModel(BaseModel):
    # expects hex string like 0xabc... representing 32 bytes
    resultHash: str




@app.get('/')
def checking_contract():
    try:
        return {"contractAddress": CONTRACT_ADDRESS,"status": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/register")
def register():
    try:
        receipt = send_transaction(contract.functions.register())
        return {"txHash": receipt.transactionHash.hex(), "status": receipt.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/submit-data")
def submit_data(payload: SubmitDataModel):
    try:
        # note: contract expects uint8 for role
        receipt = send_transaction(contract.functions.submitData(payload.role, payload.energyAmount, payload.pricePerKWh))
        return {"txHash": receipt.transactionHash.hex(), "status": receipt.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/advance-phase")
def advance_phase():
    try:
        receipt = send_transaction(contract.functions.advancePhase())
        return {"txHash": receipt.transactionHash.hex(), "status": receipt.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/hash-participants")
def hash_participants():
    try:
        # hashParticipantsList is nonpayable and modifies previousHash -> tx
        receipt = send_transaction(contract.functions.hashParticipantsList())
        return {"txHash": receipt.transactionHash.hex(), "status": receipt.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/submit-execution")
def submit_execution(payload: SubmitExecutionModel):
    try:
        # convert hex string to bytes32
        h = payload.resultHash
        if not h.startswith("0x"):
            raise ValueError("resultHash must be 0x-prefixed hex")
        # Ensure 32 bytes
        b = HexBytes(h)
        if len(b) != 32:
            raise ValueError("resultHash must be 32 bytes (64 hex chars after 0x)")
        receipt = send_transaction(contract.functions.submitExecutionResult(b))
        return {"txHash": receipt.transactionHash.hex(), "status": receipt.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/verify-execution")
def verify_execution():
    try:
        # verifyExecutionResult modifies state, so send tx
        receipt = send_transaction(contract.functions.verifyExecutionResult())
        # The contract returns (bytes32, bool) but returning via tx receipt logs is complex.
        return {"txHash": receipt.transactionHash.hex(), "status": receipt.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/participants")
def get_participants():
    try:
        total = contract.functions.TOTAL_PARTICIPANTS().call()
        result = []
        for i in range(total):
            p = contract.functions.participantsList(i).call()
            # p is (address, uint8, uint256, uint256)
            result.append({
                "index": i,
                "id": p[0],
                "role": p[1],
                "energyAmount": p[2],
                "pricePerKWh": p[3]
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/phase")
def get_phase():
    try:
        phase = contract.functions.currentPhase().call()  # uint8
        round_ = contract.functions.currentRound().call()
        return {"currentPhase": phase, "currentRound": round_}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/submitted-results")
def get_submitted_results():
    try:
        entries = []
        for i in range(5):
            r = contract.functions.submittedResults(i).call()
            entries.append({
                "index": i,
                "submitter": r[0],
                "resultHash": r[1].hex() if isinstance(r[1], (bytes, bytearray, HexBytes)) else r[1]
            })
        final = contract.functions.finalHash().call()
        return {"submittedResults": entries, "finalHash": final.hex() if isinstance(final, (bytes, bytearray, HexBytes)) else final}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)