
# import os
# import json
# import sys
# from dotenv import load_dotenv
# from web3 import Web3
# from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
# from eth_account import Account
# from decrypt_key import get_private_key,update_keystore_path_in_env
# import pexpect

# # Import nodes_to_run and ip_dict
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../quorum-ibft-chain")))
# from initial_validators import nodes_to_run, ip_dict

# update_keystore_path_in_env()

# # ===== Configuration =====
# RPC_URL = "http://100.76.91.82:22000"
# CONTRACT_NAME = "energy_trade"
# ABI_PATH = "../compiled/EnergyTrade_abi.json"
# BYTECODE_PATH = "../compiled/EnergyTrade_bytecode.txt"
# DEPLOYED_DIR = "../deployed"
# PI_PASSWORD = "Lums12345"


# # ========================== Helper Functions ==========================

# def load_env():
#     load_dotenv()


# def connect_web3(rpc_url: str) -> Web3:
#     """Connect to Web3 RPC and inject PoA middleware."""
#     w3 = Web3(Web3.HTTPProvider(rpc_url))
#     w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
#     if not w3.is_connected():
#         raise ConnectionError(f"Unable to connect to RPC at {rpc_url}")
#     return w3


# def load_contract_artifacts(abi_path: str, bytecode_path: str):
#     """Load contract ABI and bytecode."""
#     with open(abi_path, "r") as abi_file:
#         abi = json.load(abi_file)
#     with open(bytecode_path, "r") as bytecode_file:
#         bytecode = bytecode_file.read()
#     return abi, bytecode


# def get_default_account(w3: Web3) -> str:
#     """Retrieve default account from connected node."""
#     accounts = w3.eth.accounts
#     if not accounts:
#         raise ValueError("No accounts available in the node.")
#     w3.eth.default_account = accounts[0]
#     return accounts[0]


# def deploy_contract(w3: Web3, abi: dict, bytecode: str) -> str:
#     """Deploy smart contract and return address."""
#     account = Account.from_key(get_private_key())
#     deployer = account.address
#     print(f"Deploying contract from: {deployer}")

#     contract = w3.eth.contract(abi=abi, bytecode=bytecode)
#     nonce = w3.eth.get_transaction_count(deployer)
#     tx = contract.constructor().build_transaction({
#         'from': deployer,
#         'nonce': nonce,
#         'gas': 3000000,
#         'gasPrice': w3.to_wei('0', 'gwei')  # Quorum uses 0 gas price
#     })

#     signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())
#     raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
#     tx_hash = w3.eth.send_raw_transaction(raw_tx)
#     print(f"Transaction sent. Hash: {tx_hash.hex()}")

#     receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#     print(f"✅ Contract deployed at: {receipt.contractAddress}")

#     return receipt.contractAddress


# def save_contract_address_json(contract_name: str, address: str, output_dir: str):
#     """Save deployed contract address."""
#     os.makedirs(output_dir, exist_ok=True)
#     file_name = f"{contract_name}_contract_address.json"
#     path = os.path.join(output_dir, file_name)
#     with open(path, "w") as file:
#         json.dump({"contract_address": address}, file, indent=4)
#     print(f"Contract address saved to {path}")


# def scp_distribution(command, prompt_expected, prompt_password):
#     """Distribute files securely to Pis using scp."""
#     child = pexpect.spawn(command)
#     child.expect(prompt_expected)
#     child.sendline(prompt_password)
#     child.expect(pexpect.EOF)




# def generate_pis_json(output_path: str):
#     """Generate pis.json with all Pi hostnames and node info."""
#     pis_data = {}

#     for idx, node_num in enumerate(nodes_to_run):  # enumerate gives you index + node_num
#         hostname = ip_dict[node_num]
#         pis_data[hostname] = {
#             "host": f"pi_{node_num}",
#             "pi_num": node_num,
#             "hostname": hostname,
#             "node_num": idx  # index in nodes_to_run (0-based)
#         }

#     with open(output_path, "w") as f:
#         json.dump(pis_data, f, indent=4)
#     print(f"✅ pis.json generated at {output_path}")
#     return output_path


# # ========================== Main Deployment ==========================

# def main():
#     load_env()

#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     base_dir = os.path.dirname(script_dir)

#     contract_address_path = os.path.join(base_dir, "deployed/energy_trade_contract_address.json")
#     abi_path = os.path.join(base_dir, "compiled/EnergyTrade_abi.json")
#     pis_json_path = os.path.join(base_dir, "api/pis.json")

#     # Step 1: Connect to Web3 node
#     w3 = connect_web3(RPC_URL)
#     print(f"Connected to node at {RPC_URL}")

#     # Step 2: Load contract
#     abi, bytecode = load_contract_artifacts(ABI_PATH, BYTECODE_PATH)
#     account = get_default_account(w3)
#     print(f"Using account: {account}")

#     # Step 3: Deploy contract
#     contract_address = deploy_contract(w3, abi, bytecode)

#     # Step 4: Save contract address
#     save_contract_address_json(CONTRACT_NAME, contract_address, DEPLOYED_DIR)

#     # Step 5: Generate pis.json (with all Pis)
#     generate_pis_json(pis_json_path)

#     # Step 6: Send contract, abi, and pis.json to every Pi
#     for node_number in nodes_to_run:
#         hostname = ip_dict[node_number]
#         print(f"\n📦 Distributing files to {hostname}...")

#         files_to_send = [
#             (contract_address_path, "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/deployed/energy_trade_contract_address.json"),
#             (abi_path, "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/compiled/EnergyTrade_abi.json"),
#             (pis_json_path, "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/api/pis.json"),
#         ]

#         for local_file, remote_path in files_to_send:
#             command = f"scp -r {local_file} pi@{hostname}:{remote_path}"
#             prompt_expected = f"pi@{hostname}'s password: "
#             try:
#                 scp_distribution(command, prompt_expected, PI_PASSWORD)
#                 print(f"✅ Sent {os.path.basename(local_file)} to {hostname}")
#             except Exception as e:
#                 print(f"⚠️ Failed to send {local_file} to {hostname}: {e}")


# if __name__ == "__main__":
#     main()

import os
import json
import sys
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from eth_account import Account
from decrypt_key import get_private_key, update_keystore_path_in_env
import pexpect
import paramiko

# Import nodes_to_run and ip_dict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../quorum-ibft-chain")))
from initial_validators import nodes_to_run, ip_dict

update_keystore_path_in_env()
load_dotenv()  # must be called before reading any env vars

# ===== Configuration =====
RPC_URL       = "http://100.93.80.36:22000"
CONTRACT_NAME = "energy_trade"
ABI_PATH      = "../compiled/EnergyTrade_abi.json"
BYTECODE_PATH = "../compiled/EnergyTrade_bytecode.txt"
DEPLOYED_DIR  = "../deployed"
PI_USER       = "pi"
PI_PASSWORD   = "Lums12345"
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD", "12345")  # fallback matches your keystore password

# Remote keystore base path on every Pi
PI_KEYSTORE_BASE = "/home/pi/Desktop/P2PET_Dynamic/P2PET/quorum-ibft-chain"


# ========================== Helper Functions ==========================

def load_env():
    load_dotenv()


def connect_web3(rpc_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not w3.is_connected():
        raise ConnectionError(f"Unable to connect to RPC at {rpc_url}")
    return w3


def load_contract_artifacts(abi_path: str, bytecode_path: str):
    with open(abi_path, "r") as abi_file:
        abi = json.load(abi_file)
    with open(bytecode_path, "r") as bytecode_file:
        bytecode = bytecode_file.read()
    return abi, bytecode


def get_default_account(w3: Web3) -> str:
    accounts = w3.eth.accounts
    if not accounts:
        raise ValueError("No accounts available in the node.")
    w3.eth.default_account = accounts[0]
    return accounts[0]


def deploy_contract(w3: Web3, abi: dict, bytecode: str) -> str:
    account = Account.from_key(get_private_key())
    deployer = account.address
    print(f"Deploying contract from: {deployer}")

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer)
    tx = contract.constructor().build_transaction({
        'from':     deployer,
        'nonce':    nonce,
        'gas':      3000000,
        'gasPrice': w3.to_wei('0', 'gwei'),
    })

    signed_tx = w3.eth.account.sign_transaction(tx, get_private_key())
    raw_tx    = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction", None)
    tx_hash   = w3.eth.send_raw_transaction(raw_tx)
    print(f"Transaction sent. Hash: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Contract deployed at: {receipt.contractAddress}")
    return receipt.contractAddress


def save_contract_address_json(contract_name: str, address: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{contract_name}_contract_address.json")
    with open(path, "w") as f:
        json.dump({"contract_address": address}, f, indent=4)
    print(f"Contract address saved to {path}")


def scp_distribution(command, prompt_expected, prompt_password):
    child = pexpect.spawn(command)
    child.expect(prompt_expected)
    child.sendline(prompt_password)
    child.expect(pexpect.EOF)


# ========================== Eth Address Fetcher ==========================

def get_eth_address_from_pi(hostname: str, node_num: int) -> str | None:
    """
    SSH into a Pi, read its keystore (always node0/ on each Pi — each Pi
    has exactly one node folder), decrypt it, and return the checksummed
    Ethereum address.

    Returns None if anything fails (so pis.json generation still continues).
    """
    keystore_path = f"{PI_KEYSTORE_BASE}/node{node_num}/data/keystore"
    print(f"  🔑 Fetching eth_address from {hostname} (node{node_num}) ...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=PI_USER, password=PI_PASSWORD, timeout=10)

        # Get the keystore filename
        _, stdout, _ = ssh.exec_command(f"ls {keystore_path} | head -n 1")
        keystore_filename = stdout.read().decode().strip()
        if not keystore_filename:
            print(f"  ⚠️  No keystore file found at {keystore_path} on {hostname}")
            ssh.close()
            return None

        # Read keystore JSON content
        _, stdout, _ = ssh.exec_command(f"cat {keystore_path}/{keystore_filename}")
        keystore_content = stdout.read().decode().strip()
        ssh.close()

        if not keystore_content:
            print(f"  ⚠️  Empty keystore on {hostname}")
            return None

        # Decrypt to get private key → derive address
        private_key_bytes = Account.decrypt(keystore_content, ACCOUNT_PASSWORD)
        account           = Account.from_key(private_key_bytes)
        address           = account.address  # already checksummed

        print(f"  ✅ {hostname} → {address}")
        return address

    except paramiko.AuthenticationException:
        print(f"  ❌ SSH auth failed for {hostname}")
    except Exception as e:
        print(f"  ❌ Could not get eth_address from {hostname}: {e}")

    return None


# ========================== pis.json Generator ==========================


METER_PORT_MAP = {
    2: 8002,
    3: 8003,
    4: 8004,
    11: 8005,
    13: 8006,
    15: 8007
}

def generate_pis_json(output_path: str) -> str:
    """
    Generate pis.json with all Pi hostnames, node info, AND their
    Ethereum addresses (fetched live via SSH + keystore decryption).

    Shape of each entry:
    {
      "pi_2": {
        "host":        "pi_2",
        "pi_num":      2,
        "hostname":    "100.93.80.36",
        "node_num":    0,           ← index in nodes_to_run (0-based)
        "eth_address": "0xABC..."   ← checksummed address from keystore
      },
      ...
    }
    """
    pis_data = {}

    for idx, node_num in enumerate(nodes_to_run):
        hostname = ip_dict[node_num]
        key      = f"pi_{node_num}"

        eth_address = get_eth_address_from_pi(hostname, idx)

        pis_data[key] = {
            "host":        key,
            "pi_num":      node_num,
            "hostname":    hostname,
            "node_num":    idx,          # 0-based index used for RPC port offset
            "eth_address": eth_address,  # None if fetch failed — fix manually if needed
            "meter_port": METER_PORT_MAP.get(node_num)
        }

    with open(output_path, "w") as f:
        json.dump(pis_data, f, indent=4)

    print(f"\n✅ pis.json generated at {output_path}")

    # Warn about any missing addresses
    missing = [k for k, v in pis_data.items() if not v.get("eth_address")]
    if missing:
        print(f"⚠️  Missing eth_address for: {missing}")
        print("   Fill them in manually in pis.json before running /transfer.")

    return output_path


# ========================== Main Deployment ==========================

def main():
    load_env()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir   = os.path.dirname(script_dir)

    contract_address_path = os.path.join(base_dir, "deployed/energy_trade_contract_address.json")
    abi_path              = os.path.join(base_dir, "compiled/EnergyTrade_abi.json")
    pis_json_path         = os.path.join(base_dir, "api/pis.json")

    # Step 1: Connect
    w3 = connect_web3(RPC_URL)
    print(f"Connected to node at {RPC_URL}")

    # Step 2: Load contract artifacts
    abi, bytecode = load_contract_artifacts(ABI_PATH, BYTECODE_PATH)
    account = get_default_account(w3)
    print(f"Using account: {account}")

    # Step 3: Deploy contract
    contract_address = deploy_contract(w3, abi, bytecode)

    # Step 4: Save contract address locally
    save_contract_address_json(CONTRACT_NAME, contract_address, DEPLOYED_DIR)

    # Step 5: Generate pis.json (with eth_address fetched from each Pi)
    generate_pis_json(pis_json_path)

    # Step 6: Distribute files to every Pi
    for node_number in nodes_to_run:
        hostname = ip_dict[node_number]
        print(f"\n📦 Distributing files to {hostname} ...")

        files_to_send = [
            (
                contract_address_path,
                "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/deployed/energy_trade_contract_address.json",
            ),
            (
                abi_path,
                "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/compiled/EnergyTrade_abi.json",
            ),
            (
                pis_json_path,
                "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/api/pis.json",
            ),
        ]

        for local_file, remote_path in files_to_send:
            command         = f"scp -r {local_file} pi@{hostname}:{remote_path}"
            prompt_expected = f"pi@{hostname}'s password: "
            try:
                scp_distribution(command, prompt_expected, PI_PASSWORD)
                print(f"  ✅ Sent {os.path.basename(local_file)} → {hostname}")
            except Exception as e:
                print(f"  ⚠️  Failed to send {local_file} to {hostname}: {e}")


if __name__ == "__main__":
    main()