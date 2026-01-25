# import os
# import json
# import sys

# from dotenv import load_dotenv
# from web3 import Web3
# from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
# from eth_account import Account
# from decrypt_key import get_private_key,update_keystore_path_in_env
# # from ../../quorum-ibft-chain/initial_validators import nodes_to_run, ip_dict
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../quorum-ibft-chain")))
# from initial_validators import nodes_to_run, ip_dict




# update_keystore_path_in_env()


# # ===== Configuration =====
# RPC_URL = "http://100.110.53.19:22004"
# CONTRACT_NAME = "energy_trade"  # Used for output file naming
# ABI_PATH = "../compiled/EnergyTrade_abi.json"
# BYTECODE_PATH = "../compiled/EnergyTrade_bytecode.txt"
# DEPLOYED_DIR = "../deployed"


# def load_env():
#     """Load environment variables."""
#     load_dotenv()


# def connect_web3(rpc_url: str) -> Web3:
#     """Connect to the Web3 provider and inject PoA middleware."""
#     w3 = Web3(Web3.HTTPProvider(rpc_url))
#     w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
#     if not w3.is_connected():
#         raise ConnectionError(f"Unable to connect to RPC at {rpc_url}")
#     return w3


# def load_contract_artifacts(abi_path: str, bytecode_path: str) -> tuple:
#     """Load ABI and bytecode from compiled files."""
#     with open(abi_path, "r") as abi_file:
#         abi = json.load(abi_file)
#     with open(bytecode_path, "r") as bytecode_file:
#         bytecode = bytecode_file.read()
#     return abi, bytecode


# def get_default_account(w3: Web3) -> str:
#     """Retrieve and set the default account."""
#     accounts = w3.eth.accounts
#     if not accounts:
#         raise ValueError("No accounts available in the node.")
#     w3.eth.default_account = accounts[0]
#     return accounts[0]


# def deploy_contract(w3: Web3, abi: dict, bytecode: str) -> str:
#     """Deploy the smart contract and return its address."""
#     account = Account.from_key(get_private_key())
#     deployer = account.address
#     print(f"Deploying from address: {deployer}")

#     contract = w3.eth.contract(abi=abi, bytecode=bytecode)
#     nonce = w3.eth.get_transaction_count(deployer)
#     tx = contract.constructor().build_transaction({
#         'from': deployer,
#         'nonce': nonce,
#         'gas': 3000000,
#         'gasPrice': w3.to_wei('0', 'gwei')  # Quorum uses 0 gasPrice
#     })

#     # Sign transaction
#     signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())

#     # Send transaction
#     # raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
#     # tx_hash = w3.eth.send_raw_transaction(raw_tx)
    
#     tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
#     print(f"Transaction sent. Hash: {tx_hash.hex()}")

#     # Wait for receipt
#     receipt = w3.eth.wait_for_transaction_receipt(tx_hash,timeout=300)
#     print(f"Contract deployed at address: {receipt.contractAddress}")

#     return receipt.contractAddress


#     # contract = w3.eth.contract(abi=abi, bytecode=bytecode)
#     # tx_hash = contract.constructor().transact()
#     # tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#     # return tx_receipt.contractAddress


# def save_contract_address_json(contract_name: str, address: str, output_dir: str):
#     """Save deployed contract address in a JSON file named after the contract."""
#     os.makedirs(output_dir, exist_ok=True)
#     file_name = f"{contract_name}_contract_address.json"
#     path = os.path.join(output_dir, file_name)
#     with open(path, "w") as file:
#         json.dump({"contract_address": address}, file, indent=4)
#     print(f"Contract address saved to {path}")

# def scp_distribution(command, prompt_expected, prompt_password):
#     """This method is used distribute files to Raspberry Pis using secure copy (scp) command"""

#     import pexpect

#     # Spawn a child process
#     child = pexpect.spawn(command)

#     # Wait for the password prompt and send the password
#     child.expect(prompt_expected)
#     child.sendline(prompt_password)

#     # Wait for the process to complete
#     child.expect(pexpect.EOF)


# def main():

#     load_env()

#     pi_password = 'Lums12345'

#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     contract_address_path = os.path.join(os.path.dirname(script_dir), 'deployed/energy_trade_contract_address.json')
#     abi_path = os.path.join(os.path.dirname(script_dir), 'compiled/EnergyTrade_abi.json')

#     w3 = connect_web3(RPC_URL)
#     print(f"Connected to node at {RPC_URL}")

#     abi, bytecode = load_contract_artifacts(ABI_PATH, BYTECODE_PATH)
#     account = get_default_account(w3)
#     print(f"Using account: {account}")

#     contract_address = deploy_contract(w3, abi, bytecode)
#     print(f"Contract deployed at: {contract_address}")

#     save_contract_address_json(CONTRACT_NAME, contract_address, DEPLOYED_DIR)

#     for node_number in nodes_to_run:
#         command = f"scp -r {contract_address_path} pi@{ip_dict[node_number]}:/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/deployed/energy_trade_contract_address.json"
#         prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
#         scp_distribution(command, prompt_expected, pi_password)

#         command = f"scp -r {abi_path} pi@{ip_dict[node_number]}:/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/compiled/EnergyTrade_abi.json"
#         prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
#         scp_distribution(command, prompt_expected, pi_password)

#         command = f"ssh pi@{ip_dict[node_number]} 'echo {nodes_to_run.index(node_number)} > /home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/api/NodeNum.txt'"
#         prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
#         scp_distribution(command, prompt_expected, pi_password)


# if __name__ == "__main__":
#     main()




# # # # ===== Configuration =====
# # RPC_URL = "http://100.110.53.19:22004"
# # CONTRACT_NAME = "energy_trade"  # Used for output file naming
# # ABI_PATH = "../compiled/EnergyTrade_abi.json"
# # BYTECODE_PATH = "../compiled/EnergyTrade_bytecode.txt"
# # DEPLOYED_DIR = "../deployed"


# # def connect_web3(rpc_url: str) -> Web3:
# #     """Connect to the Web3 provider and inject PoA middleware."""
# #     w3 = Web3(Web3.HTTPProvider(rpc_url))
# #     w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
# #     if not w3.is_connected():
# #         raise ConnectionError(f"Unable to connect to RPC at {rpc_url}")
# #     return w3


# # def load_contract_artifacts(abi_path: str, bytecode_path: str) -> tuple:
# #     """Load ABI and bytecode from compiled files."""
# #     with open(abi_path, "r") as abi_file:
# #         abi = json.load(abi_file)
# #     with open(bytecode_path, "r") as bytecode_file:
# #         bytecode = bytecode_file.read()
# #     return abi, bytecode


# # def get_default_account(w3: Web3) -> str:
# #     """Retrieve and set the default account."""
# #     accounts = w3.eth.accounts
# #     if not accounts:
# #         raise ValueError("No accounts available in the node.")
# #     w3.eth.default_account = accounts[0]
# #     return accounts[0]

# # def deploy_contract(w3: Web3, abi: dict, bytecode: str) -> str:
# #     """Deploy the smart contract and return its address, with auto-mining fallback."""
# #     account = Account.from_key(get_private_key())
# #     deployer = account.address
# #     print(f"Deploying from address: {deployer}")

# #     # --- Check if deployer is validator ---
# #     validators = w3.geth.istanbul.get_validators()
# #     is_validator = deployer.lower() in [v.lower() for v in validators]

# #     if is_validator:
# #         print("✅ Deployer is a validator. Mining rights confirmed.")
# #     else:
# #         print("⚠️ Deployer is NOT a validator. Will temporarily start mining on this node if possible.")

# #     contract = w3.eth.contract(abi=abi, bytecode=bytecode)
# #     nonce = w3.eth.get_transaction_count(deployer)
# #     tx = contract.constructor().build_transaction({
# #         'from': deployer,
# #         'nonce': nonce,
# #         'gas': 3000000,
# #         'gasPrice': w3.to_wei('0', 'gwei')
# #     })

# #     signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())
# #     raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
# #     tx_hash = w3.eth.send_raw_transaction(raw_tx)
# #     print(f"Transaction sent. Hash: {tx_hash.hex()}")

# #     # --- If not validator, try mining manually ---
# #     if not is_validator:
# #         try:
# #             print("⛏️ Starting miner to include transaction...")
# #             w3.geth.miner.start(1)
# #             print("...miner started.")
# #         except Exception as e:
# #             print(f"⚠️ Could not start miner automatically: {e}")

# #     try:
# #         # Wait longer for slow Raspberry Pi nodes
# #         receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
# #         print(f"✅ Contract deployed at address: {receipt.contractAddress}")
# #     except Exception as e:
# #         print(f"❌ Deployment failed or timed out: {e}")
# #         if not is_validator:
# #             try:
# #                 print("Stopping miner...")
# #                 w3.geth.miner.stop()
# #             except:
# #                 pass
# #         raise

# #     # --- Stop miner if it was started here ---
# #     if not is_validator:
# #         try:
# #             print("🛑 Stopping miner...")
# #             w3.geth.miner.stop()
# #         except Exception as e:
# #             print(f"⚠️ Could not stop miner: {e}")

# #     return receipt.contractAddress

# # def load_env():
# #     """Load environment variables."""
# #     load_dotenv()


# # def main():
# #     load_env()
# #     pi_password = 'Lums12345'

# #     script_dir = os.path.dirname(os.path.abspath(__file__))
# #     contract_address_path = os.path.join(os.path.dirname(script_dir), 'deployed/energy_trade_contract_address.json')
# #     abi_path = os.path.join(os.path.dirname(script_dir), 'compiled/EnergyTrade_abi.json')

# #     w3 = connect_web3(RPC_URL)
# #     print(f"Connected to node at {RPC_URL}")

# #     # --- Debug info ---
# #     # coinbase = w3.eth.coinbase
# #     # coinbase = w3.eth.get_coinbase()
# #     coinbase = w3.geth.miner.get_coinbase()
# #     validators = w3.geth.istanbul.get_validators()
# #     print(f"Node coinbase (miner): {coinbase}")
# #     print(f"Validator set: {validators}")

# #     abi, bytecode = load_contract_artifacts(ABI_PATH, BYTECODE_PATH)
# #     account = get_default_account(w3)
# #     print(f"Using account: {account}")

# #     contract_address = deploy_contract(w3, abi, bytecode)
# #     print(f"Contract deployed at: {contract_address}")

# #     save_contract_address_json(CONTRACT_NAME, contract_address, DEPLOYED_DIR)

# #     for node_number in nodes_to_run:
# #         command = f"scp -r {contract_address_path} pi@{ip_dict[node_number]}:/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/deployed/energy_trade_contract_address.json"
# #         prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
# #         scp_distribution(command, prompt_expected, pi_password)

# #         command = f"scp -r {abi_path} pi@{ip_dict[node_number]}:/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/compiled/EnergyTrade_abi.json"
# #         prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
# #         scp_distribution(command, prompt_expected, pi_password)

# #         command = f"ssh pi@{ip_dict[node_number]} 'echo {nodes_to_run.index(node_number)} > /home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/api/NodeNum.txt'"
# #         prompt_expected = f"pi@{ip_dict[node_number]}'s password: "
# #         scp_distribution(command, prompt_expected, pi_password)
# # if __name__ == "__main__":
# #     main()

import os
import json
import sys
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from eth_account import Account
from decrypt_key import get_private_key,update_keystore_path_in_env
import pexpect

# Import nodes_to_run and ip_dict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../quorum-ibft-chain")))
from initial_validators import nodes_to_run, ip_dict

update_keystore_path_in_env()

# ===== Configuration =====

RPC_URL = "http://100.93.80.36:22000"
CONTRACT_NAME = "energy_trade"
ABI_PATH = "../compiled/EnergyTrade_abi.json"
BYTECODE_PATH = "../compiled/EnergyTrade_bytecode.txt"
DEPLOYED_DIR = "../deployed"
PI_PASSWORD = "Lums12345"


# ========================== Helper Functions ==========================

def load_env():
    load_dotenv()


def connect_web3(rpc_url: str) -> Web3:
    """Connect to Web3 RPC and inject PoA middleware."""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not w3.is_connected():
        raise ConnectionError(f"Unable to connect to RPC at {rpc_url}")
    return w3


def load_contract_artifacts(abi_path: str, bytecode_path: str):
    """Load contract ABI and bytecode."""
    with open(abi_path, "r") as abi_file:
        abi = json.load(abi_file)
    with open(bytecode_path, "r") as bytecode_file:
        bytecode = bytecode_file.read()
    return abi, bytecode


def get_default_account(w3: Web3) -> str:
    """Retrieve default account from connected node."""
    accounts = w3.eth.accounts
    if not accounts:
        raise ValueError("No accounts available in the node.")
    w3.eth.default_account = accounts[0]
    return accounts[0]


def deploy_contract(w3: Web3, abi: dict, bytecode: str) -> str:
    """Deploy smart contract and return address."""
    account = Account.from_key(get_private_key())
    deployer = account.address
    print(f"Deploying contract from: {deployer}")

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer)
    tx = contract.constructor().build_transaction({
        'from': deployer,
        'nonce': nonce,
        'gas': 3000000,
        'gasPrice': w3.to_wei('0', 'gwei')  # Quorum uses 0 gas price
    })

    signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())
    raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    print(f"Transaction sent. Hash: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Contract deployed at: {receipt.contractAddress}")

    return receipt.contractAddress


def save_contract_address_json(contract_name: str, address: str, output_dir: str):
    """Save deployed contract address."""
    os.makedirs(output_dir, exist_ok=True)
    file_name = f"{contract_name}_contract_address.json"
    path = os.path.join(output_dir, file_name)
    with open(path, "w") as file:
        json.dump({"contract_address": address}, file, indent=4)
    print(f"Contract address saved to {path}")


def scp_distribution(command, prompt_expected, prompt_password):
    """Distribute files securely to Pis using scp."""
    child = pexpect.spawn(command)
    child.expect(prompt_expected)
    child.sendline(prompt_password)
    child.expect(pexpect.EOF)


# def generate_pis_json(output_path: str):
#     """Generate pis.json with all Pi hostnames and node info."""
#     pis_data = {}

#     for node_num in nodes_to_run:
#         hostname = ip_dict[node_num]
#         pis_data[hostname] = {
#             "host": f"pi_{node_num}",
#             "node_num": node_num
#         }

#     with open(output_path, "w") as f:
#         json.dump(pis_data, f, indent=4)
#     print(f"✅ pis.json generated at {output_path}")
#     return output_path

def generate_pis_json(output_path: str):
    """Generate pis.json with all Pi hostnames and node info."""
    pis_data = {}

    for idx, node_num in enumerate(nodes_to_run):  # enumerate gives you index + node_num
        hostname = ip_dict[node_num]
        pis_data[hostname] = {
            "host": f"pi_{node_num}",
            "pi_num": node_num,
            "hostname": hostname,
            "node_num": idx  # index in nodes_to_run (0-based)
        }

    with open(output_path, "w") as f:
        json.dump(pis_data, f, indent=4)
    print(f"✅ pis.json generated at {output_path}")
    return output_path


# ========================== Main Deployment ==========================

def main():
    load_env()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    contract_address_path = os.path.join(base_dir, "deployed/energy_trade_contract_address.json")
    abi_path = os.path.join(base_dir, "compiled/EnergyTrade_abi.json")
    pis_json_path = os.path.join(base_dir, "api/pis.json")

    # Step 1: Connect to Web3 node
    w3 = connect_web3(RPC_URL)
    print(f"Connected to node at {RPC_URL}")

    # Step 2: Load contract
    abi, bytecode = load_contract_artifacts(ABI_PATH, BYTECODE_PATH)
    account = get_default_account(w3)
    print(f"Using account: {account}")

    # Step 3: Deploy contract
    contract_address = deploy_contract(w3, abi, bytecode)

    # Step 4: Save contract address
    save_contract_address_json(CONTRACT_NAME, contract_address, DEPLOYED_DIR)

    # Step 5: Generate pis.json (with all Pis)
    generate_pis_json(pis_json_path)

    # Step 6: Send contract, abi, and pis.json to every Pi
    for node_number in nodes_to_run:
        hostname = ip_dict[node_number]
        print(f"\n📦 Distributing files to {hostname}...")

        files_to_send = [
            (contract_address_path, "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/deployed/energy_trade_contract_address.json"),
            (abi_path, "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/compiled/EnergyTrade_abi.json"),
            (pis_json_path, "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/api/pis.json"),
        ]

        for local_file, remote_path in files_to_send:
            command = f"scp -r {local_file} pi@{hostname}:{remote_path}"
            prompt_expected = f"pi@{hostname}'s password: "
            try:
                scp_distribution(command, prompt_expected, PI_PASSWORD)
                print(f"✅ Sent {os.path.basename(local_file)} to {hostname}")
            except Exception as e:
                print(f"⚠️ Failed to send {local_file} to {hostname}: {e}")


if __name__ == "__main__":
    main()
