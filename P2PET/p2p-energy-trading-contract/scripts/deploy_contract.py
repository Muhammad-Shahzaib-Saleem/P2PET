import os
import json
import sys

from dotenv import load_dotenv
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from eth_account import Account
from decrypt_key import get_private_key
# from ../../quorum-ibft-chain/initial_validators import nodes_to_run, ip_dict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../quorum-ibft-chain")))
from initial_validators import nodes_to_run, ip_dict







# ===== Configuration =====
RPC_URL = "http://127.0.0.1:22000"
CONTRACT_NAME = "energy_trade"  # Used for output file naming
ABI_PATH = "../compiled/EnergyTrade_abi.json"
BYTECODE_PATH = "../compiled/EnergyTrade_bytecode.txt"
DEPLOYED_DIR = "../deployed"


def load_env():
    """Load environment variables."""
    load_dotenv()


def connect_web3(rpc_url: str) -> Web3:
    """Connect to the Web3 provider and inject PoA middleware."""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not w3.is_connected():
        raise ConnectionError(f"Unable to connect to RPC at {rpc_url}")
    return w3


def load_contract_artifacts(abi_path: str, bytecode_path: str) -> tuple:
    """Load ABI and bytecode from compiled files."""
    with open(abi_path, "r") as abi_file:
        abi = json.load(abi_file)
    with open(bytecode_path, "r") as bytecode_file:
        bytecode = bytecode_file.read()
    return abi, bytecode


def get_default_account(w3: Web3) -> str:
    """Retrieve and set the default account."""
    accounts = w3.eth.accounts
    if not accounts:
        raise ValueError("No accounts available in the node.")
    w3.eth.default_account = accounts[0]
    return accounts[0]


def deploy_contract(w3: Web3, abi: dict, bytecode: str) -> str:
    """Deploy the smart contract and return its address."""
    account = Account.from_key(get_private_key())
    deployer = account.address
    print(f"Deploying from address: {deployer}")

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer)
    tx = contract.constructor().build_transaction({
        'from': deployer,
        'nonce': nonce,
        'gas': 3000000,
        'gasPrice': w3.to_wei('0', 'gwei')  # Quorum uses 0 gasPrice
    })

    # Sign transaction
    signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())

    # Send transaction
    raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    # tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_Transaction)
    print(f"Transaction sent. Hash: {tx_hash.hex()}")

    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Contract deployed at address: {receipt.contractAddress}")

    return receipt.contractAddress


    # contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    # tx_hash = contract.constructor().transact()
    # tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # return tx_receipt.contractAddress


def save_contract_address_json(contract_name: str, address: str, output_dir: str):
    """Save deployed contract address in a JSON file named after the contract."""
    os.makedirs(output_dir, exist_ok=True)
    file_name = f"{contract_name}_contract_address.json"
    path = os.path.join(output_dir, file_name)
    with open(path, "w") as file:
        json.dump({"contract_address": address}, file, indent=4)
    print(f"Contract address saved to {path}")

def scp_distribution(command, prompt_expected, prompt_password):
    """This method is used distribute files to Raspberry Pis using secure copy (scp) command"""

    import pexpect

    # Spawn a child process
    child = pexpect.spawn(command)

    # Wait for the password prompt and send the password
    child.expect(prompt_expected)
    child.sendline(prompt_password)

    # Wait for the process to complete
    child.expect(pexpect.EOF)


def main():

    load_env()

    pi_password = 'Lums12345'

    script_dir = os.path.dirname(os.path.abspath(__file__))
    contract_address_path = os.path.join(os.path.dirname(script_dir), 'deployed/energy_trade_contract_address.json')
    abi_path = os.path.join(os.path.dirname(script_dir), 'compiled/EnergyTrade_abi.json')

    w3 = connect_web3(RPC_URL)
    print(f"Connected to node at {RPC_URL}")

    abi, bytecode = load_contract_artifacts(ABI_PATH, BYTECODE_PATH)
    account = get_default_account(w3)
    print(f"Using account: {account}")

    contract_address = deploy_contract(w3, abi, bytecode)
    print(f"Contract deployed at: {contract_address}")

    save_contract_address_json(CONTRACT_NAME, contract_address, DEPLOYED_DIR)

    for node_number in nodes_to_run:
        command = f"scp -r {contract_address_path} pi@{ip_dict[node_number]}:/home/pi/P2PET/p2p-energy-trading-contract/deployed/energy_trade_contract_address.json"
        prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
        scp_distribution(command, prompt_expected, pi_password)

        command = f"scp -r {abi_path} pi@{ip_dict[node_number]}:/home/pi/P2PET/p2p-energy-trading-contract/compiled/EnergyTrade_abi.json"
        prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
        scp_distribution(command, prompt_expected, pi_password)


if __name__ == "__main__":
    main()

