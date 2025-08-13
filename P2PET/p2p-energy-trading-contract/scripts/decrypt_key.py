import json
import os
from eth_account import Account
from dotenv import load_dotenv
import glob


def update_keystore_path_in_env():
    """
    Finds the latest UTC keystore file inside the first 'node*' directory
    and updates the KEYSTORE_PATH in the .env file.
    """
    # Locate .env file (relative to this script)
    # env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
    env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

    # Detect the first node directory (node0, node1, etc.)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../quorum-ibft-chain"))
    node_dirs = glob.glob(os.path.join(base_dir, "node*"))
    if not node_dirs:
        raise FileNotFoundError(f"No node directories found in {base_dir}")

    # Prefer node0 if it exists, else pick the first available node
    node0_path = os.path.join(base_dir, "node0")
    if node0_path in node_dirs:
        node_dir = node0_path
    else:
        node_dir = sorted(node_dirs)[0]  # Pick the first available node in sorted order

    print(f"[INFO] Using node directory: {node_dir}")

    # Find the latest UTC keystore file
    keystore_dir = os.path.join(node_dir, "data", "keystore")
    keystore_files = glob.glob(os.path.join(keystore_dir, "UTC--*"))
    if not keystore_files:
        raise FileNotFoundError(f"No UTC keystore files found in {keystore_dir}")

    latest_keystore = max(keystore_files, key=os.path.getmtime)

    latest_keystore_rel = os.path.relpath(latest_keystore, start=os.path.dirname(__file__))

    # Update .env with the correct KEYSTORE_PATH
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    with open(env_file, "w") as f:
        found_key = False
        for line in lines:
            if line.startswith("KEYSTORE_PATH="):
                f.write(f"KEYSTORE_PATH={latest_keystore_rel}\n")
                found_key = True
            else:
                f.write(line)
        if not found_key:
            f.write(f"KEYSTORE_PATH={latest_keystore_rel}\n")

    print(f"[INFO] Updated .env with KEYSTORE_PATH={latest_keystore_rel}")
    return latest_keystore_rel


def get_private_key():
    # Load environment variables
    load_dotenv()

    KEYSTORE_PATH = os.getenv("KEYSTORE_PATH")
    ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")

    if not KEYSTORE_PATH or not ACCOUNT_PASSWORD:
        raise ValueError("Missing KEYSTORE_PATH or ACCOUNT_PASSWORD in environment variables.")

    # Read keystore file
    with open(KEYSTORE_PATH, "r") as f:
        keystore = json.load(f)

    # Decrypt private key
    try:
        private_key_bytes = Account.decrypt(keystore, ACCOUNT_PASSWORD)
        private_key_hex = private_key_bytes.hex()
        return private_key_hex
    except Exception as e:
        raise ValueError(f"Failed to decrypt private key: {str(e)}")