#!/usr/bin/env python3
import os, time
import json
from web3 import Web3
# from web3.middleware import geth_poa_middleware
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from dotenv import load_dotenv
from web3.exceptions import ContractLogicError
from decrypt_key import get_private_key, update_keystore_path_in_env

update_keystore_path_in_env()

# Load .env
load_dotenv()

# Load config from .env
# RPC_URL = os.getenv("RPC_URL")
RPC_URL = "http://127.0.0.1:22000"
ABI_PATH = os.getenv("ABI_PATH")
CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")

# Read deployed contract address
if CONTRACT_ADDRESS_PATH is None:
    raise FileNotFoundError("CONTRACT_ADDRESS_PATH is not set in .env or environment variables")

with open(CONTRACT_ADDRESS_PATH, "r") as f:
    data = json.load(f)
    CONTRACT_ADDRESS = data["contract_address"]

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Set up account
account = w3.eth.account.from_key(get_private_key())
sender_address = account.address

# Load ABI
with open(ABI_PATH, "r") as f:
    abi = json.load(f)

# Contract instance
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

PHASE_NAMES = {
    0: "DataSubmission",
    1: "Execution",
    2: "Trading",
}


def send_transaction(function_call):
    nonce = w3.eth.get_transaction_count(sender_address)

    tx = function_call.build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': 0
    })

    signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())
    raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    # tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    print(f"Transaction sent: {tx_hash.hex()} — waiting for receipt...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Check if transaction failed (status == 0)
    if receipt.status == 0:
        print("Transaction failed.")

        # Simulate the transaction with eth_call to extract revert reason
        try:
            tx_call = {
                'to': tx['to'],
                'from': sender_address,
                'data': tx['data'],
                'gas': tx['gas']
            }
            # eth_call simulates the transaction and returns the revert reason
            revert_msg = w3.eth.call(tx_call, block_identifier=receipt.blockNumber)
            print("Unknown failure reason.")
        except ContractLogicError as e:
            # Extract only the human-readable revert message
            message = str(e)
            if message.startswith("execution reverted:"):
                clean_msg = message.split("execution reverted:")[1].strip()
                print(f"Revert reason: {clean_msg}")
            else:
                print(f"Revert reason: {message}")
        except Exception as e:
            print(f"Failed to decode revert reason: {e}")

    return receipt


def register():
    print("Registering participant...")
    receipt = send_transaction(contract.functions.register())
    if receipt.status == 1:
        print("Participant registered successfully.")
    print(f"Registration TX Hash: {receipt.transactionHash.hex()}")


def submit_data(role: int, energy: int, price_wei: int):
    print("Submitting energy data...")
    receipt = send_transaction(contract.functions.submitData(role, energy, price_wei))
    if receipt.status == 1:
        print("Energy data submitted successfully.")
    print(f"Data Submission TX: {receipt.transactionHash.hex()}")


def hash_participants():
    print("Hashing participants list...")

    # Fetching the hash computed i.e., the participant list hash
    try:
        current_hash = contract.functions.hashParticipantsList().call({'from': sender_address})
        print(f"Computed Hash: {current_hash.hex()}")
    except Exception as e:
        print(f"Failed to fetch hash from cotract: {e}")
        return

    # Actual transaction hash
    receipt = send_transaction(contract.functions.hashParticipantsList())
    if receipt:
        print(f"Hashed Participants TX hash: {receipt.transactionHash.hex()}")


def advance_phase():
    print("Advancing to next phase...")
    receipt = send_transaction(contract.functions.advancePhase())
    if not receipt:
        print("No receipt; Advance phase failed")
        return

    if receipt.status != 1:
        print("advancePhase transaction reverted; phase not changed.")
        return

    print(f"Advance Phase TX hash: {receipt.transactionHash.hex()}")

    # Read the updated phase and round
    try:
        current_phase = contract.functions.currentPhase().call()
        current_round = contract.functions.currentRound().call()
        phase_name = PHASE_NAMES.get(current_phase, f"Unknown({current_phase})")
        print(f"New Phase: {phase_name}, Round: {current_round}")
    except Exception as e:
        print(f"Error reading phase/round: {e}")


def verify_execution():
    print("Sending verifyExecutionResult transaction...")
    receipt = send_transaction(contract.functions.verifyExecutionResult())
    if not receipt:
        print("No receipt; something went wrong with sending.")
        return
    if receipt.status != 1:
        print("verifyExecutionResult transaction reverted.")
        return

    # Read back the stored result (state was updated by the successful tx)
    try:
        maj_h, verified = contract.functions.verifyExecutionResult().call({'from': sender_address})
        print(f"Final hash: majorityHash={maj_h.hex()}, isVerified={verified}")
    except Exception as e:
        print("Failed to read back result:", e)


def get_final_hash():
    try:
        final_hash_bytes = contract.functions.finalHash().call()
        final_hash_hex = final_hash_bytes.hex()
        print(f"Final Hash: {final_hash_hex}")
        return final_hash_hex
    except Exception as e:
        print(f"Error retrieving finalHash: {e}")
        return None


SCALING_FACTOR = 100  # For 2 decimal places (e.g., 0.75 to 75)


def scale(value):
    return int(value * SCALING_FACTOR)


if __name__ == "__main__":
    try:
        # Example flow; adapt/order as needed
        register()
        # submit_data(role=2, energy=scale(100), price_wei=scale(10))
        # submit_data(role=2, energy=scale(90), price_wei=scale(15))
        # submit_data(role=1, energy=scale(95), price_wei=scale(20))
        # submit_data(role=1, energy=scale(105), price_wei=scale(25))
        # hash_participants()
        # advance_phase()  # move into next phase
        # verify_execution()
        # get_final_hash()
    except Exception as e:
        print(f"Error occurred: {e}")
