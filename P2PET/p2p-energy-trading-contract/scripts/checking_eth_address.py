import paramiko
from eth_account import Account
import os
from dotenv import load_dotenv
load_dotenv()

ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD", "")
PI_KEYSTORE_BASE = "/home/pi/Desktop/P2PET_Dynamic/P2PET/quorum-ibft-chain"

pis = [
    {"hostname": "100.93.80.36",    "name": "pi_2",  "idx": 0},
    {"hostname": "100.120.139.128", "name": "pi_11", "idx": 1},
    {"hostname": "100.80.11.48",    "name": "pi_13", "idx": 2},
    {"hostname": "100.120.124.29",  "name": "pi_15", "idx": 3},
]

PI_USER     = "pi"
PI_PASSWORD = "Lums12345"

for pi in pis:
    print(f"\n{'='*50}")
    print(f"[{pi['name']}] {pi['hostname']}")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(pi["hostname"], username=PI_USER, password=PI_PASSWORD, timeout=10)

        keystore_path = f"{PI_KEYSTORE_BASE}/node{pi['idx']}/data/keystore"
        print(f"  keystore_path: {keystore_path}")

        _, stdout, stderr = ssh.exec_command(f"ls {keystore_path}")
        ls_out = stdout.read().decode().strip()
        ls_err = stderr.read().decode().strip()
        print(f"  ls out: '{ls_out}'")
        print(f"  ls err: '{ls_err}'")

        if ls_out:
            _, stdout, _ = ssh.exec_command(f"cat {keystore_path}/{ls_out.splitlines()[0]}")
            content = stdout.read().decode().strip()
            print(f"  keystore (first 80 chars): {content[:80]}")
            print(f"  ACCOUNT_PASSWORD: '{ACCOUNT_PASSWORD}'")

            try:
                pk  = Account.decrypt(content, ACCOUNT_PASSWORD)
                acc = Account.from_key(pk)
                print(f"  ✅ Address: {acc.address}")
            except Exception as e:
                print(f"  ❌ Decrypt error: {e}")
        ssh.close()

    except Exception as e:
        print(f"  ❌ SSH/outer error: {e}")