import subprocess
import glob
import os
from eth_account import Account
# Path to keystore file
keystore_files = glob.glob("../../quorum-ibft-chain/node*/data/keystore/*")

if not keystore_files:
    raise FileNotFoundError("No keystore file found in quorum-ibft-chain node directories.")

keystore_path = keystore_files[0]

# Read the keystore content
keystore = subprocess.check_output(f"cat {keystore_path}", shell=True, text=True).strip()



private_key_bytes = Account.decrypt(keystore, "12345")
PRIVATE_KEY = private_key_bytes.hex()

print(keystore)
print("Privat Key :", PRIVATE_KEY)
