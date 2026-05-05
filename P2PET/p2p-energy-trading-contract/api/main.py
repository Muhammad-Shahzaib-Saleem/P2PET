# #source ../../pi-venv/bin/activate
# from multiprocessing import pool
# import subprocess
# from eth_account import Account
# import os, time
# import json
# from web3 import Web3
# # from web3.middleware import geth_poa_middleware
# from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
# from web3.exceptions import ContractLogicError
# import socket
# from fastapi import FastAPI, HTTPException
# import sys
# from dotenv import load_dotenv
# from fetch_and_match import run_matching_and_get_hash
# from pathlib import Path
# import paramiko
# from fastapi.middleware.cors import CORSMiddleware
# import requests

# import time
# import atexit
# import threading
# from contextlib import asynccontextmanager
# import concurrent.futures
# from typing import List, Dict, Any
# from collections import defaultdict

# from eth_utils import to_checksum_address



# MATCH_FILE = "matching_result.json"

# # GPIO.setmode(GPIO.BCM)
# # GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)

# load_dotenv()


# def load_matches():
#     with open(MATCH_FILE) as f:
#         return json.load(f)







# PI_NODES = [
#     {"name": "pi_2",  "host": "100.93.80.36",      "username": "pi", "password": "Lums12345", "port": 8002},
#     {"name": "pi_3",  "host": "100.71.238.87",   "username": "pi", "password": "Lums12345", "port": 8003},
#     {"name": "pi_4",  "host": "100.80.205.106", "username": "pi", "password": "Lums12345", "port": 8004},
#     {"name": "pi_11",  "host": "100.120.139.128", "username": "pi", "password": "Lums12345", "port": 8005},
#     {"name": "pi_13",  "host": "100.80.11.48",   "username": "pi", "password": "Lums12345", "port": 8006},
#     {"name": "pi_15",  "host": "100.120.124.29", "username": "pi", "password": "Lums12345", "port": 8007},
    
# ]

# ROLE_MAP = {
#     "buyer": 1,
#     "seller": 2
# }

# SCALING_FACTOR = 1000

# PI_PROJECT_DIR  = "/home/pi/Desktop/P2PET_Dynamic/P2PET"
# PI_VENV_ACTIVATE = f"source {PI_PROJECT_DIR}/venv/bin/activate"
# PI_API_DIR       = f"{PI_PROJECT_DIR}/p2p-energy-trading-contract/api"




# with open("NodeNum.txt", "r") as f:
#     node_number = int(f.read().strip())

# rpc_port_num = 22000

# RPC_URL = f"http://{'100.120.139.128'}:{str(rpc_port_num+node_number)}"

# # RPC_URL = f"https://100.110.53.19:22004"
# # LOCAL_RPC_URL = "https://127.0.0.1:22000"
# # LOCAL_PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")
# ABI_PATH = os.getenv("ABI_PATH")

# # Keystore and contract details
# keystore = subprocess.check_output(
#     "cd ..; cd ..; cd quorum-ibft-chain; cd node*; cd data/keystore; cat $(ls | head -n 1)",
#     shell=True,
#     text=True,
# ).strip()

# ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")
# PI_PASSWORD = "Lums12345"


# with open(CONTRACT_ADDRESS_PATH, "r") as f:
#     data = json.load(f)
#     CONTRACT_ADDRESS = data["contract_address"]


# with open(ABI_PATH, "r") as abi_file:
#     abi = json.load(abi_file)


# try:
#     private_key_bytes = Account.decrypt(keystore, ACCOUNT_PASSWORD)
#     PRIVATE_KEY = private_key_bytes.hex()
# except Exception as e:
#     raise RuntimeError(f"Failed to decrypt private key: {e}")

# # Web3 instance
# # Web3 instance
# w3 = Web3(Web3.HTTPProvider(RPC_URL))
# w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# # Set up account
# account = w3.eth.account.from_key(PRIVATE_KEY)
# sender_address = account.address

# # Contract instance
# contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)


# RESULT_FILE              = "match_result.json"   # matching algorithm output
# PIS_JSON_PATH            = "pis.json"      # must include "eth_address" per Pi
# METER_API_PORT           = 8002            # default meter_api port on each Pi
# TRANSFER_POLL_INTERVAL_S = 2              # seconds between status polls
# TRANSFER_TIMEOUT_S       = 300            # 5-minute hard timeout per transfer



# def start_pi(node: dict) -> bool:
#     name, host, username, password, port = (
#         node["name"], node["host"], node["username"], node["password"], node["port"]
#     )
#     print(f"[{name}] Connecting to {host} ...")
#     client = paramiko.SSHClient()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     try:
#         client.connect(hostname=host, username=username, password=password, timeout=10)
#     except Exception as e:
#         print(f"[{name}] ❌ SSH failed: {e}")
#         return False

#     # Kill any old instance on that port
#     _, stdout, _ = client.exec_command(f"fuser -k {port}/tcp 2>/dev/null || true")
#     stdout.channel.recv_exit_status()
#     time.sleep(0.5)

#     start_cmd = (
#         f"cd {PI_API_DIR} && "
#         f"{PI_VENV_ACTIVATE} && "
#         f"nohup python meter_api.py --port {port} > meter_{port}.log 2>&1 &"
#     )
#     _, stdout, _ = client.exec_command(start_cmd)
#     stdout.channel.recv_exit_status()
#     time.sleep(3)

#     _, stdout, _ = client.exec_command("pgrep -fa meter_api.py")
#     running = bool(stdout.read().decode().strip())
#     client.close()

#     if running:
#         print(f"[{name}] ✅  http://{host}:{port}")
#     else:
#         print(f"[{name}] ❌ Process did not start")
#     return running

# def start_all_pis():
#     print("\n🚀 Starting meter_api.py on all Pi nodes...")
#     for node in PI_NODES:
#         start_pi(node)
#     print("✅ Pi startup sequence complete.\n")


# # ─── Phase Keeper Bot ─────────────────────────────────────────────────────────



# transfer_deadlines: dict[int, float] = {}
# transfer_deadlines_lock = threading.Lock()

# TRANSFER_WINDOW_SECONDS = 60 * 60  # 60 minutes

# PHASE_NAMES = {
#     0: "DataSubmission  [ 5 min]",
#     1: "Execution       [ 5 min]",
#     2: "EnergyTransfer  [50 min on-chain | 60 min window]",
# }


# # def phase_keeper_loop():
# #     """
# #     Timeline per round (60 min total on-chain):
# #         T+00  DataSubmission starts        (5 min)
# #         T+05  Execution starts             (5 min)
# #         T+10  EnergyTransfer starts        (50 min on-chain)
# #               └─ Round N transfer window opens (60 min = closes at T+70)
# #         T+60  Round ends → Round N+1 DataSubmission starts
# #               └─ Round N transfer window still open (10 min left)
# #         T+65  Round N+1 Execution starts
# #               └─ Round N transfer window still open (5 min left)
# #         T+70  Round N+1 EnergyTransfer starts
# #               └─ Round N transfer window CLOSES ✓
# #               └─ Round N+1 transfer window opens (closes at T+130)
# #     """
# #     print("⏰ Phase keeper bot started.")
# #     print("   DataSubmission(5m) → Execution(5m) → EnergyTransfer(50m) = 60 min round")
# #     print("   Transfer window = 60 min (overlaps 10 min into next round)\n")

# #     while True:
# #         try:
# #             time_left     = contract.functions.timeRemaining().call()
# #             round_left    = contract.functions.roundTimeRemaining().call()
# #             current_phase = contract.functions.currentPhase().call()
# #             current_round = contract.functions.currentRound().call()

# #             print(
# #                 f"\n[Keeper] Round {current_round} | {PHASE_NAMES.get(current_phase)}"
# #                 f"\n         Phase left: {_fmt(time_left)} | Round left: {_fmt(round_left)}"
# #             )

# #             # Report all open transfer windows (could be current + previous round)
# #             _report_open_windows(current_round)

# #             if time_left == 0:
# #                 print(f"[Keeper] ⏰ Phase timer expired — advancing...")
# #                 receipt = send_transaction(contract.functions.advancePhase())

# #                 if receipt.status == 1:
# #                     new_phase = contract.functions.currentPhase().call()
# #                     new_round = contract.functions.currentRound().call()

# #                     if new_round > current_round:
# #                         print(f"[Keeper] 🔄 Round {current_round} complete → Round {new_round} started!")

# #                     print(f"[Keeper] ✅ Now: Round {new_round} | {PHASE_NAMES.get(new_phase)}")

# #                     # Execution just ended → open 60-min transfer window for this round
# #                     if new_phase == 2:  # entered EnergyTransfer
# #                         deadline = time.time() + TRANSFER_WINDOW_SECONDS
# #                         with transfer_deadlines_lock:
# #                             transfer_deadlines[current_round] = deadline

# #                         print(
# #                             f"[Keeper] 🔋 Round {current_round} transfer window opened!"
# #                             f"\n         Closes at {_ts(deadline)} — "
# #                             f"10 min overlap into Round {current_round + 1}"
# #                         )

# #                     elif new_phase == 0:
# #                         # Round just rolled over — check if previous round window is still open
# #                         prev = new_round - 1
# #                         remaining = get_transfer_window_remaining(prev)
# #                         if remaining > 0:
# #                             print(
# #                                 f"[Keeper] ⚠️  Round {prev} transfer window still open! "
# #                                 f"{_fmt(remaining)} remaining (overlap period)"
# #                             )
# #                         print(f"[Keeper] 📋 Round {new_round} DataSubmission open.")

# #                     elif new_phase == 1:
# #                         prev = new_round - 1
# #                         remaining = get_transfer_window_remaining(prev)
# #                         if remaining > 0:
# #                             print(
# #                                 f"[Keeper] ⚠️  Round {prev} transfer window still open! "
# #                                 f"{_fmt(remaining)} remaining — closes when this Execution ends"
# #                             )
# #                         print(f"[Keeper] ⚙️  Round {new_round} Execution open.")

# #                 else:
# #                     print("[Keeper] ❌ advancePhase() transaction failed.")

# #         except Exception as e:
# #             print(f"[Keeper] ❌ Error: {e}")

# #         time.sleep(30)  # poll every 30s — safe for 5-min phases


# def phase_keeper_loop():
#     """
#     Timeline per round (60 min total on-chain):
#         T+00  DataSubmission starts        (10 min)
#         T+10  Execution starts             (10 min)
#         T+20  EnergyTransfer starts        (40 min on-chain)
#               └─ Round N transfer window opens (60 min = closes at T+80)
#               └─ /transfer endpoint auto-triggered here
#         T+60  Round ends → Round N+1 DataSubmission starts
#               └─ Round N transfer window still open (20 min left)
#         T+80  Round N+1 EnergyTransfer starts
#               └─ Round N transfer window CLOSES
#     """
#     print("⏰ Phase keeper bot started.")
#     print("   DataSubmission(10m) → Execution(10m) → EnergyTransfer(40m) = 60 min round")
#     print("   Transfer window = 60 min (overlaps 20 min into next round)\n")

#     FAST_POLL_THRESHOLD  = 60   # switch to fast poll in last 60s
#     FAST_POLL_INTERVAL   = 2    # poll every 2s when close to expiry
#     NORMAL_POLL_INTERVAL = 30   # poll every 30s normally

#     while True:
#         try:
#             time_left     = contract.functions.timeRemaining().call()
#             round_left    = contract.functions.roundTimeRemaining().call()
#             current_phase = contract.functions.currentPhase().call()
#             current_round = contract.functions.currentRound().call()

#             print(
#                 f"\n[Keeper] Round {current_round} | {PHASE_NAMES.get(current_phase)}"
#                 f"\n         Phase left: {_fmt(time_left)} | Round left: {_fmt(round_left)}"
#             )

#             _report_open_windows(current_round)

#             if time_left == 0:
#                 print(f"[Keeper] ⏰ Phase timer expired — advancing...")
#                 receipt = send_transaction(contract.functions.advancePhase())

#                 if receipt.status == 1:
#                     new_phase = contract.functions.currentPhase().call()
#                     new_round = contract.functions.currentRound().call()

#                     if new_round > current_round:
#                         print(f"[Keeper] 🔄 Round {current_round} complete → Round {new_round} started!")

#                     print(f"[Keeper] ✅ Now: Round {new_round} | {PHASE_NAMES.get(new_phase)}")

#                     # ── EnergyTransfer phase just started ──────────────────
#                     if new_phase == 2:
#                         # 1. Record 60-min transfer deadline
#                         deadline = time.time() + TRANSFER_WINDOW_SECONDS
#                         with transfer_deadlines_lock:
#                             transfer_deadlines[current_round] = deadline

#                         print(
#                             f"[Keeper] 🔋 Round {current_round} transfer window opened!"
#                             f"\n         Closes at {_ts(deadline)} — "
#                             f"20 min overlap into Round {current_round + 1}"
#                         )

#                         # 2. Auto-trigger /transfer endpoint in background thread
#                         #    (background so it doesn't block the keeper loop)
#                         transfer_thread = threading.Thread(
#                             target=_auto_trigger_transfer,
#                             args=(current_round,),
#                             daemon=True
#                         )
#                         transfer_thread.start()

#                     elif new_phase == 0:
#                         prev = new_round - 1
#                         remaining = get_transfer_window_remaining(prev)
#                         if remaining > 0:
#                             print(
#                                 f"[Keeper] ⚠️  Round {prev} transfer window still open! "
#                                 f"{_fmt(remaining)} remaining (overlap period)"
#                             )
#                         print(f"[Keeper] 📋 Round {new_round} DataSubmission open.")

#                     elif new_phase == 1:
#                         prev = new_round - 1
#                         remaining = get_transfer_window_remaining(prev)
#                         if remaining > 0:
#                             print(
#                                 f"[Keeper] ⚠️  Round {prev} transfer window still open! "
#                                 f"{_fmt(remaining)} remaining — closes when this Execution ends"
#                             )
#                         print(f"[Keeper] ⚙️  Round {new_round} Execution open.")

#                 else:
#                     print("[Keeper] ❌ advancePhase() transaction failed.")

#                 sleep_time = NORMAL_POLL_INTERVAL

#             elif time_left <= FAST_POLL_THRESHOLD:
#                 print(f"[Keeper] ⚡ {time_left}s left — fast polling ({FAST_POLL_INTERVAL}s)")
#                 sleep_time = FAST_POLL_INTERVAL

#             else:
#                 sleep_time = NORMAL_POLL_INTERVAL

#         except Exception as e:
#             print(f"[Keeper] ❌ Error: {e}")
#             sleep_time = NORMAL_POLL_INTERVAL

#         time.sleep(sleep_time)


# # def _auto_trigger_transfer(round_number: int):
# #     """
# #     Called in a background thread when EnergyTransfer phase starts.
# #     Hits the /transfer endpoint on localhost.
# #     Retries up to 3 times if it fails.
# #     """
# #     MAX_RETRIES = 3
# #     RETRY_DELAY = 5  # seconds between retries

# #     print(f"[AutoTransfer] 🚀 Round {round_number} — triggering /transfer endpoint...")

# #     for attempt in range(1, MAX_RETRIES + 1):
# #         try:
# #             resp = requests.post(
# #                 "http://localhost:8000/transfer",
# #                 timeout=300  # 5 min timeout — transfers can take a while
# #             )

# #             if resp.status_code == 200:
# #                 data = resp.json()
# #                 print(
# #                     f"[AutoTransfer] ✅ Round {round_number} transfer complete!"
# #                     f"\n               Total: {data.get('total_matches')} | "
# #                     f"Succeeded: {data.get('succeeded')} | "
# #                     f"Failed: {data.get('failed')}"
# #                 )

# #                 # Log per-match results
# #                 for r in data.get("results", []):
# #                     seller_reason = r.get("seller_status", {}).get("stop_reason", "?")
# #                     buyer_reason  = r.get("buyer_status",  {}).get("stop_reason", "?")
# #                     error         = r.get("error")
# #                     if error:
# #                         print(f"[AutoTransfer]   ❌ {r.get('seller')} → {r.get('buyer')}: {error}")
# #                     else:
# #                         print(
# #                             f"[AutoTransfer]   {'✅' if seller_reason == 'THRESHOLD_REACHED' else '⚠️ '} "
# #                             f"{r.get('seller')} → {r.get('buyer')} | "
# #                             f"seller: {seller_reason} | buyer: {buyer_reason}"
# #                         )
# #                 return  # success — done

# #             else:
# #                 print(
# #                     f"[AutoTransfer] ⚠️  Attempt {attempt}/{MAX_RETRIES} — "
# #                     f"HTTP {resp.status_code}: {resp.text[:200]}"
# #                 )

# #         except requests.exceptions.Timeout:
# #             print(f"[AutoTransfer] ⏱️  Attempt {attempt}/{MAX_RETRIES} — request timed out")

# #         except requests.exceptions.ConnectionError as e:
# #             print(f"[AutoTransfer] 🔌 Attempt {attempt}/{MAX_RETRIES} — connection error: {e}")

# #         except Exception as e:
# #             print(f"[AutoTransfer] ❌ Attempt {attempt}/{MAX_RETRIES} — unexpected error: {e}")

# #         if attempt < MAX_RETRIES:
# #             print(f"[AutoTransfer] 🔁 Retrying in {RETRY_DELAY}s...")
# #             time.sleep(RETRY_DELAY)

# #     print(f"[AutoTransfer] ❌ Round {round_number} — all {MAX_RETRIES} attempts failed.")

# def _auto_trigger_transfer(round_number: int):
#     """
#     Called in a background thread when EnergyTransfer phase starts.
#     Hits the /transfer endpoint on localhost.
#     Retries up to 3 times if it fails.
#     """
#     MAX_RETRIES = 3
#     RETRY_DELAY = 5

#     print(f"[AutoTransfer] 🚀 Round {round_number} — triggering /transfer endpoint...")

#     for attempt in range(1, MAX_RETRIES + 1):
#         try:
#             resp = requests.post(
#                 "http://localhost:8000/transfer",
#                 timeout=300
#             )

#             if resp.status_code == 200:
#                 data = resp.json()
#                 print(
#                     f"[AutoTransfer] ✅ Round {round_number} transfer complete!"
#                     f"\n               Total: {data.get('total_matches')} | "
#                     f"Succeeded: {data.get('succeeded')} | "
#                     f"Failed: {data.get('failed')}"
#                 )

#                 # Log per-match results safely
#                 for r in data.get("results", []):
#                     error = r.get("error")

#                     # ── safely extract stop reasons (status may be None) ──
#                     seller_status = r.get("seller_status") or {}
#                     buyer_status  = r.get("buyer_status")  or {}
#                     seller_reason = seller_status.get("stop_reason", "no_status")
#                     buyer_reason  = buyer_status.get("stop_reason",  "no_status")

#                     # ── also extract any nested errors ───────────────────
#                     seller_error  = seller_status.get("error")
#                     buyer_error   = buyer_status.get("error")

#                     if error:
#                         # match-level error (e.g. Pi not found in pis.json)
#                         print(f"[AutoTransfer]   ❌ {r.get('seller')} → {r.get('buyer')}: {error}")

#                     else:
#                         success = (
#                             seller_reason == "THRESHOLD_REACHED"
#                             and buyer_reason == "THRESHOLD_REACHED"
#                         )
#                         icon = "✅" if success else "⚠️ "
#                         print(
#                             f"[AutoTransfer]   {icon} "
#                             f"{r.get('seller')} → {r.get('buyer')} | "
#                             f"energy: {r.get('energy_kwh')} kWh | "
#                             f"seller: {seller_reason} | buyer: {buyer_reason}"
#                         )

#                         # show nested errors if any
#                         if seller_error:
#                             print(f"[AutoTransfer]      seller error: {seller_error}")
#                         if buyer_error:
#                             print(f"[AutoTransfer]      buyer error:  {buyer_error}")

#                 return  # success — done

#             else:
#                 print(
#                     f"[AutoTransfer] ⚠️  Attempt {attempt}/{MAX_RETRIES} — "
#                     f"HTTP {resp.status_code}: {resp.text[:200]}"
#                 )

#         except requests.exceptions.Timeout:
#             print(f"[AutoTransfer] ⏱️  Attempt {attempt}/{MAX_RETRIES} — request timed out")

#         except requests.exceptions.ConnectionError as e:
#             print(f"[AutoTransfer] 🔌 Attempt {attempt}/{MAX_RETRIES} — connection error: {e}")

#         except Exception as e:
#             print(f"[AutoTransfer] ❌ Attempt {attempt}/{MAX_RETRIES} — unexpected error: {e}")

#         if attempt < MAX_RETRIES:
#             print(f"[AutoTransfer] 🔁 Retrying in {RETRY_DELAY}s...")
#             time.sleep(RETRY_DELAY)

#     print(f"[AutoTransfer] ❌ Round {round_number} — all {MAX_RETRIES} attempts failed.")


# # ─── Transfer window helpers (call from your off-chain transfer logic) ─────────

# def is_transfer_window_open(round_number: int) -> bool:
#     """
#     Gate check for off-chain transfer logic.
#     Round N's window is open for 60 min starting from when Round N's Execution ended.
#     Closes exactly when Round N+1's EnergyTransfer starts.
#     """
#     return get_transfer_window_remaining(round_number) > 0


# def get_transfer_window_remaining(round_number: int) -> float:
#     """Returns seconds remaining in a round's transfer window. 0.0 if closed or not opened."""
#     with transfer_deadlines_lock:
#         deadline = transfer_deadlines.get(round_number)
#     if deadline is None:
#         return 0.0
#     return max(0.0, deadline - time.time())


# def _report_open_windows(current_round: int):
#     """Log all rounds that currently have an open transfer window."""
#     now = time.time()
#     with transfer_deadlines_lock:
#         open_windows = [
#             (rnd, deadline)
#             for rnd, deadline in transfer_deadlines.items()
#             if deadline > now
#         ]

#     if not open_windows:
#         print("[Keeper]    No transfer windows currently open.")
#         return

#     for rnd, deadline in sorted(open_windows):
#         remaining = deadline - now
#         tag = ""
#         if rnd < current_round:
#             tag = f" 🔁 overlap — {_fmt(remaining)} left before closing"
#         elif rnd == current_round:
#             tag = f" ✅ active — {_fmt(remaining)} remaining"
#         print(f"[Keeper] 🔋 Round {rnd} transfer window:{tag} (closes {_ts(deadline)})")


# # ─── Formatting helpers ────────────────────────────────────────────────────────

# def _fmt(seconds) -> str:
#     """Seconds → mm:ss string."""
#     m, s = divmod(int(seconds), 60)
#     return f"{m:02d}:{s:02d}"


# def _ts(unix_ts: float) -> str:
#     """Unix timestamp → HH:MM:SS string."""
#     return time.strftime("%H:%M:%S", time.localtime(unix_ts))






# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Start Pi nodes in background
#     pi_thread = threading.Thread(target=start_all_pis, daemon=True)
#     pi_thread.start()

#     # Start phase keeper bot in background   <-- ADD THIS
#     keeper_thread = threading.Thread(target=phase_keeper_loop, daemon=True)
#     keeper_thread.start()

#     yield
#     # teardown (optional)
# # app
# app = FastAPI(title="P2P Energy Trading API", lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # or specify ["http://localhost:5173"] for stricter control
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# def get_local_ip():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try:
#         s.connect(('192.168.0.1', 80))
#         return s.getsockname()[0]
#     finally:
#         s.close()



# import json


# def load_bidding_results():
#     if not os.path.exists(RESULT_FILE):
#         return []
    
#     with open(RESULT_FILE, "r") as file:
#         data = json.load(file)
    
#     return data


# def get_pi_hostname(host, file_path='pis.json'):
#     """
#     Given a host name, return its hostname and user from pis.json.
    
#     Args:
#         host (str): The host key (e.g., "pi_1", "pi_4Ethernet").
#         file_path (str): Path to the pis.json file.
    
#     Returns:
#         dict: A dictionary with 'hostname' and 'user' if found, else None.
#     """
#     try:
#         with open(file_path, 'r') as f:
#             pis = json.load(f)

#         for pi in pis:
#             if pi['host'] == host:
#                 return {"hostname": pi['hostname']}
        
#         print(f"Host '{host}' not found in {file_path}")
#         return None

#     except FileNotFoundError:
#         print(f"Error: File '{file_path}' not found.")
#         return None
#     except json.JSONDecodeError:
#         print(f"Error: '{file_path}' is not a valid JSON file.")
#         return None










# def get_dynamic_private_key(node_number, base_dir="/home/pi/Desktop/P2PET_Dynamic/P2PET/quorum-ibft-chain",
#                              account_password=ACCOUNT_PASSWORD, remote_host=None, remote_user="pi", remote_password=PI_PASSWORD):
#     """
#     Decrypts and returns the private key for a given node number.
#     Works locally or remotely (via SSH with password authentication).
#     """
#     try:
#         node_path = Path(base_dir) / f"node{node_number}" / "data" / "keystore"

#         # --- 🔹 Remote access using paramiko (no password prompt) ---
#         if remote_host:
#             print(f"🔄 Fetching keystore from remote Pi: {remote_host}")

#             ssh = paramiko.SSHClient()
#             ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#             ssh.connect(remote_host, username=remote_user, password=remote_password)

#             # Get keystore filename
#             stdin, stdout, stderr = ssh.exec_command(f"ls {node_path} | head -n 1")
#             keystore_filename = stdout.read().decode().strip()
#             if not keystore_filename:
#                 raise FileNotFoundError(f"No keystore file found at {node_path}")

#             # Read keystore content directly (no file saving)
#             stdin, stdout, stderr = ssh.exec_command(f"cat {node_path}/{keystore_filename}")
#             keystore_content = stdout.read().decode()
#             ssh.close()

#         # --- 🔹 Local mode ---
#         else:
#             keystore_files = list(node_path.glob("*"))
#             if not keystore_files:
#                 raise FileNotFoundError(f"No keystore files found in {node_path}")
#             with open(keystore_files[0], "r") as f:
#                 keystore_content = f.read()

#         # --- 🔹 Decrypt private key ---
#         private_key_bytes = Account.decrypt(keystore_content, account_password)
#         private_key_hex = private_key_bytes.hex()
#         print(f"✅ Successfully decrypted private key for node{node_number}")

#         return private_key_hex

#     except Exception as e:
#         raise RuntimeError(f"Failed to get private key for node {node_number}: {e}")

# # dynamic_private_key=get_dynamic_private_key(0, remote_host="100.76.91.82")
# # print("Private Key",dynamic_private_key)



# def get_web3_rpc(hostname, pis_json_path="pis.json"):
#     """Creates a Web3 connection and contract instance dynamically using pis.json."""
#     try:
#         # Load pis.json
#         with open(pis_json_path, "r") as f:
#             pis_data = json.load(f)

#         # Ensure hostname exists in pis.json
#         if hostname not in pis_data:
#             raise HTTPException(status_code=404, detail=f"Hostname {hostname} not found in pis.json")

#         node_info = pis_data[hostname]
#         node_number = node_info["node_num"]
#         node_hostname = node_info["hostname"]

#         # Build dynamic RPC URL
#         RPC_URL = f"http://{node_hostname}:{rpc_port_num + node_number}"
#         print(f"Connecting to RPC: {RPC_URL}")

#         # Connect to Web3
#         w3 = Web3(Web3.HTTPProvider(RPC_URL))
#         w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

#         if not w3.is_connected():
#             raise Exception(f"Cannot connect to {RPC_URL}")


#         # Get dynamic private key
#         dynamic_private_key = get_dynamic_private_key(node_number, remote_host=node_hostname)  

#         # Load sender account
#         account = w3.eth.account.from_key(dynamic_private_key)
#         sender_address = account.address

#         # Load contract instance
#         contract = w3.eth.contract(
#             address=Web3.to_checksum_address(CONTRACT_ADDRESS),
#             abi=abi
#         )

#         print(f"Connected successfully to node {node_number} ({hostname})")
#         return w3, contract, sender_address,dynamic_private_key

#     except FileNotFoundError:
#         raise HTTPException(status_code=500, detail="pis.json file not found")
#     except KeyError as e:
#         raise HTTPException(status_code=500, detail=f"Missing key in pis.json: {e}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error initializing Web3: {e}")


# def send_transaction(function_call):
#     nonce = w3.eth.get_transaction_count(sender_address)

#     tx = function_call.build_transaction({
#         'from': sender_address,
#         'nonce': nonce,
#         'gas': 500000,
#         'gasPrice': 0
#     })

#     signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

#     # Use correct attribute name for Web3.py v6+
#     tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

#     print(f"Transaction sent: {tx_hash.hex()} — waiting for receipt...")
#     receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

#     if receipt.status == 0:
#         print("Transaction failed.")
#         try:
#             tx_call = {
#                 'to': tx['to'],
#                 'from': sender_address,
#                 'data': tx['data'],
#                 'gas': tx['gas']
#             }
#             revert_msg = w3.eth.call(tx_call, block_identifier=receipt.blockNumber)
#             print("Unknown failure reason.")
#         except ContractLogicError as e:
#             message = str(e)
#             if message.startswith("execution reverted:"):
#                 clean_msg = message.split("execution reverted:")[1].strip()
#                 print(f"Revert reason: {clean_msg}")
#             else:
#                 print(f"Revert reason: {message}")
#         except Exception as e:
#             print(f"Failed to decode revert reason: {e}")

#     return receipt



# def send_transaction_dynamic(w3, sender_address, function_call, dynamic_private_key):
#     """Sends a transaction to the blockchain and returns receipt + revert reason if failed."""
#     revert_reason = None
#     try:
#         nonce = w3.eth.get_transaction_count(sender_address)

#         tx = function_call.build_transaction({
#             'from': sender_address,
#             'nonce': nonce,
#             'gas': 500000,
#             'gasPrice': 0
#         })

#         signed_tx = w3.eth.account.sign_transaction(tx, dynamic_private_key)
#         tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

#         print(f"Transaction sent: {tx_hash.hex()} — waiting for receipt...")
#         receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

#         if receipt.status == 0:
#             print("Transaction failed.")
#             try:
#                 tx_call = {
#                     'to': tx['to'],
#                     'from': sender_address,
#                     'data': tx['data'],
#                     'gas': tx['gas']
#                 }
#                 # Try to trigger the revert reason by simulating the call
#                 w3.eth.call(tx_call, block_identifier=receipt.blockNumber)
#             except ContractLogicError as e:
#                 message = str(e)
#                 if message.startswith("execution reverted:"):
#                     revert_reason = message.split("execution reverted:")[1].strip()
#                     print(f"Revert reason: {revert_reason}")
#                 else:
#                     revert_reason = message
#                     print(f"Revert reason: {revert_reason}")
#             except Exception as e:
#                 revert_reason = f"Failed to decode revert reason: {e}"
#                 print(revert_reason)

#         return receipt, revert_reason

#     except Exception as e:
#         print(f"Error sending transaction: {e}")
#         raise HTTPException(status_code=500, detail=f"Error sending transaction: {e}")



# @app.get('/')
# def checking_contract():
#     try:
#         return {"health":"ok","status": True,"version":"2.0.0","description":"This is P2P Energy trading contract api (Endoints)"}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# print("Contract Address:",CONTRACT_ADDRESS)
# @app.get('/contract')
# def checking_contract():
#     try:
#         return {"contractAddress": CONTRACT_ADDRESS,"status": True}
    
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @app.get('/private-key')
# def checking_contract():
#     try:
#         return {"Private Keys": PRIVATE_KEY,"status": True}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @app.get('/dynamic_private-key/{hostname}')
# def dynamic_key(hostname: str):
#     try:
#         _, _, _, dynamic_private_key = get_web3_rpc(hostname)
#         return {"Dynamic Private Key": dynamic_private_key, "status": True}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @app.get("/transfer/window/remaining")
# def get_transfer_window_remaining_endpoint():
#     """
#     Returns remaining transfer window time for the PREVIOUS round.
#     Transfer window only starts after Execution phase ends (EnergyTransfer phase begins).
    
#     - Round 1, Phase 0 or 1  → not started yet
#     - Round 1, Phase 2       → Round 1 window running (60 min)
#     - Round 2, Phase 0 or 1  → Round 1 window still has time (overlap)
#     - Round 2, Phase 2       → Round 1 window closed, Round 2 window running
#     """
#     try:
#         current_round = contract.functions.currentRound().call()
#         current_phase = contract.functions.currentPhase().call()
#         phase_names   = {0: "DataSubmission", 1: "Execution", 2: "EnergyTransfer"}

#         # Phase 0 or 1 of Round 1 → transfer hasn't started at all yet
#         if current_round == 1 and current_phase in (0, 1):
#             return {
#                 "status":             "not_started",
#                 "message":            "Transfer window has not opened yet. Waiting for Round 1 Execution to complete.",
#                 "currentRound":       current_round,
#                 "currentPhase":       phase_names[current_phase],
#                 "isOpen":             False,
#                 "remainingSeconds":   0,
#                 "remainingFormatted": "00:00",
#                 "transferRound":      None,
#             }

#         # Phase 2 of any round → current round's window is running
#         if current_phase == 2:
#             target_round = current_round
#         # Phase 0 or 1 of Round 2+ → previous round's window is in overlap
#         else:
#             target_round = current_round - 1

#         # Get remaining time
#         remaining_onchain  = contract.functions.transferWindowRemaining(target_round).call()
#         remaining_offchain = get_transfer_window_remaining(target_round)
#         remaining          = max(int(remaining_onchain), int(remaining_offchain))
#         is_open            = remaining > 0

#         return {
#             "status":             "open" if is_open else "closed",
#             "message":            (
#                 f"Round {target_round} transfer window {'is open' if is_open else 'has closed'}."
#                 + (f" Overlapping into Round {current_round}." if target_round < current_round and is_open else "")
#             ),
#             "currentRound":       current_round,
#             "currentPhase":       phase_names[current_phase],
#             "isOpen":             is_open,
#             "transferRound":      target_round,
#             "remainingSeconds":   remaining,
#             "remainingFormatted": _fmt(remaining),
#             "closesAt":           _ts(time.time() + remaining) if remaining > 0 else "closed",
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# @app.post("/dynamic_register")
# def register_participant(hostname: str):
#     """Registers participant dynamically based on Pi hostname."""
#     try:
#         w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
#         function_call = contract.functions.register()

#         receipt, revert_reason = send_transaction_dynamic(w3, sender_address, function_call, dynamic_private_key)

#         if receipt.status == 1:
#             return {"status": "success", "txHash": receipt.transactionHash.hex()}
#         else:
#             reason = revert_reason or "Transaction reverted or failed."
#             raise HTTPException(status_code=400, detail={"status": "failed", "reason": reason})

#     except HTTPException:
#         raise  # re-raise our controlled exceptions
#     except Exception as e:
#         revert_reason = str(e)
#         if "execution reverted" in revert_reason:
#             start = revert_reason.find("execution reverted")
#             revert_reason = revert_reason[start:]
#         raise HTTPException(
#             status_code=400,
#             detail={"status": "failed", "reason": revert_reason}
#         )




# @app.post("/register")
# def register_participant():
#     receipt = send_transaction(contract.functions.register())
#     if receipt.status == 1:
#         return {"status": "success", "message": "Transaction successful."}
#     else:
#         raise HTTPException(status_code=400, detail="Transaction failed.")


# @app.post("/submit-data")
# def submit_data(role:int, energy:int, price:int):
#     receipt = send_transaction(contract.functions.submitData(role, energy, price))
#     if receipt.status == 1:
#         return {"status": "success", "message": "Transaction successful."}
#     else:
#         raise HTTPException(status_code=400, detail="Transaction failed.")



# def scale(value):
#     return int(float(value) * SCALING_FACTOR)


# @app.post("/dynamic_submit_data")
# def submit_data(hostname: str, role: str, energy: float, price: float):
#     """Submits participant data dynamically and returns success or revert reason."""

#     role_normalized = role.strip().lower()
#     if role_normalized not in ROLE_MAP:
#         raise HTTPException(status_code=400, detail="Invalid role")

#     role_int = ROLE_MAP[role_normalized]

#     # ✅ scale ONCE here
#     energy_scaled = scale(energy)
#     price_scaled = scale(price)

#     try:
#         w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)

#         function_call = contract.functions.submitData(
#             role_int,
#             energy_scaled,
#             price_scaled
#         )

#         receipt, revert_reason = send_transaction_dynamic(
#             w3, sender_address, function_call, dynamic_private_key
#         )

#         if receipt.status == 1:
#             return {
#                 "status": "success",
#                 "message": "Transaction successful.",
#                 "txHash": receipt.transactionHash.hex(),
#             }
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail={
#                     "status": "failed",
#                     "reason": revert_reason or "Transaction reverted or failed.",
#                     "txHash": receipt.transactionHash.hex() if receipt else None,
#                 },
#             )

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "status": "error",
#                 "message": str(e),
#             },
#         )


# # def scale(value):
# #     return int(value * SCALING_FACTOR)

# # @app.post("/dynamic_submit_data")
# # def submit_data(hostname: str, role: str, energy: int, price: int):
# #     """Submits participant data dynamically and returns success or revert reason."""
# #     role_normalized = role.strip().lower()
# #     if role_normalized not in ROLE_MAP:
# #         raise HTTPException(status_code=400, detail="Invalid role")

# #     role_int = ROLE_MAP[role_normalized]
# #     energy_scaled = scale(energy)
# #     price_scaled = scale(price)

# #     try:
# #         w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
# #         function_call = contract.functions.submitData(role_int, energy_scaled, price_scaled)

# #         receipt, revert_reason = send_transaction_dynamic(
# #             w3, sender_address, function_call, dynamic_private_key
# #         )

# #         if receipt.status == 1:
# #             return {
# #                 "status": "success",
# #                 "message": "Transaction successful.",
# #                 "txHash": receipt.transactionHash.hex(),
# #             }
# #         else:
# #             raise HTTPException(
# #                 status_code=400,
# #                 detail={
# #                     "status": "failed",
# #                     "reason": revert_reason or "Transaction reverted or failed.",
# #                     "txHash": receipt.transactionHash.hex() if receipt else None,
# #                 },
# #             )

# #     except HTTPException:
# #         # Pass through known errors
# #         raise
# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail={
# #                 "status": "error",
# #                 "message": f"Unexpected error occurred: {str(e)}",
# #             },
# #         )
# #     raise HTTPException(status_code=400, detail="Transaction failed.")





# @app.post("/Dynamic_hash_participants")
# def hash_participants(hostname: str):
#     try:
#         # 🔹 Step 1: Get web3, contract, sender, and private key
#         w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)

#         # 🔹 Step 2: Prepare function call
#         function_call = contract.functions.hashParticipantsList()

#         # 🔹 Step 3: Send transaction using dynamic signing function
#         receipt, revert_reason = send_transaction_dynamic(
#             w3, sender_address, function_call, dynamic_private_key
#         )

#         # 🔹 Step 4: Fetch the latest computed hash from contract state
#         latest_hash = contract.functions.previousHash().call()

#         # 🔹 Step 5: Handle transaction result
#         if receipt.status == 1:
#             tx_hash = receipt.transactionHash.hex()
#             return {
#                 "status": "success",
#                 "message": "✅ Hash calculated and submitted successfully.",
#                 "computedHash": latest_hash.hex(),
#                 "txHash": tx_hash
#             }
#         else:
#             reason = revert_reason or "Transaction failed without revert reason."
#             raise HTTPException(status_code=400, detail={"reason": reason})

#     except HTTPException:
#         # rethrow HTTP exceptions cleanly
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")







# @app.post("/dynamic_advance_phase")
# def advance_phase(hostname: str):
#     try:
#         w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
#         function_call = contract.functions.advancePhase()

#         # Send transaction using dynamic private key
#         receipt, revert_reason = send_transaction_dynamic(
#             w3, sender_address, function_call, dynamic_private_key
#         )

#          # Replace if using another network

#         # Fetch current phase and round
#         current_phase = contract.functions.currentPhase().call()
#         current_round = contract.functions.currentRound().call()
#         phase_name = PHASE_NAMES.get(current_phase, f"Unknown({current_phase})")

#         if receipt.status == 1:
#             return {
#                 "status": "success",
#                 "message": "Phase advanced successfully.",
#                 "currentRound": current_round,
#                 "phaseName": phase_name,
#                 "txHash": receipt.transactionHash.hex(),
#                 "revert_reason": revert_reason
#             }
#         else:
#             return {
#                 "status": "failed",
#                 "message": "Transaction failed.",
#                 "currentRound": current_round,
#                 "phaseName": phase_name,
#                 "txHash": receipt.transactionHash.hex(),
#                 "revert_reason": revert_reason or "Transaction failed without revert reason"
#             }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))




# @app.post("/dynamic_submit_execution_result")
# def dynamic_submit_execution_result(hostname: str):
#     try:
#         w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
#         participant_count, result_hash_hex = run_matching_and_get_hash(contract)

#         # Build bytes32-compatible hash
#         hash_bytes32 = Web3.to_bytes(hexstr="0x" + result_hash_hex)

#         function_call = contract.functions.submitExecutionResult(hash_bytes32)
#         print("Participant Count:", participant_count)
#         # Send transaction using the dynamic private key method
#         receipt, revert_reason = send_transaction_dynamic(
#             w3, sender_address, function_call, dynamic_private_key
#         )

#         explorer_url = f"https://etherscan.io/tx/{receipt.transactionHash.hex()}"  # Replace with proper chain explorer if needed

#         if receipt.status == 1:
#             return {
#                 "status": "success",
#                 "participants": participant_count,
#                 "result_hash": f"0x{result_hash_hex}",
#                 "txHash": receipt.transactionHash.hex(),
#                 "explorerUrl": explorer_url,
#                 "revert_reason": revert_reason
#             }
#         else:
#             return {
#                 "status": "failed",
#                 "participants": participant_count,
#                 "result_hash": f"0x{result_hash_hex}",
#                 "txHash": receipt.transactionHash.hex(),
#                 "explorerUrl": explorer_url,
#                 "revert_reason": revert_reason or "Transaction failed without revert reason"
#             }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))








# @app.post("/verify_execution")
# def verify_execution():
#     receipt = send_transaction(contract.functions.verifyExecutionResult())
#     if receipt.status == 1:
#         return {"status": "success", "message": "Transaction successful."}
#     else:
#         raise HTTPException(status_code=400, detail="Transaction failed.")
    






# @app.post("/dynamic_verify_execution")
# def dynamic_verify_execution(hostname: str):
#     try:
#         w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
#         # Get return values using a call (doesn't change state)
#         majority_hash, is_verified = contract.functions.verifyExecutionResult().call({'from': sender_address})
#         function_call = contract.functions.verifyExecutionResult()

#         # Send transaction dynamically
#         receipt, revert_reason = send_transaction_dynamic(
#             w3, sender_address, function_call, dynamic_private_key
#         )

 
#         if receipt.status == 1:
#             return {
#                 "status": "success",
#                 "message": "Execution verified successfully.",
#                 "txHash": receipt.transactionHash.hex(),
#                 "majority_hash": majority_hash.hex(),  # convert bytes32 to hex
#                 "is_verified": is_verified,
#                 "revert_reason": revert_reason
#             }
#         else:
#             return {
#                 "status": "failed",
#                 "message": "Transaction failed.",
#                 "txHash": receipt.transactionHash.hex(),
                
#                 "revert_reason": revert_reason or "Transaction failed without revert reason"
#             }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))




# @app.get("/total_participants")
# def get_total_participants():
#     try:
#         value = contract.functions.TOTAL_PARTICIPANTS().call()
#         return {"TOTAL_PARTICIPANTS": value}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))




# @app.get("/participants_list")
# def get_participants_list():
#     try:
#         total = contract.functions.TOTAL_PARTICIPANTS().call()
#         participants = []
#         for i in range(1,total):
#             data = contract.functions.participantsList(i).call()
#             participants.append(data)
#         return {"participantsList": participants}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/address_to_slot/{address}")
# def get_address_to_slot(address: str):
#     try:
#         checksum_addr = Web3.to_checksum_address(address)
#         slot = contract.functions.addressToSlot(checksum_addr).call()
#         return {"address": checksum_addr, "slot": slot}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/next_available_slot")
# def get_next_available_slot():
#     try:
#         slot = contract.functions.nextAvailableSlot().call()
#         return {"nextAvailableSlot": slot}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    

# @app.get("/remaining_time_in_phase")
# def get_remaining_time_in_phase():
#     try:
#         remaining_time = contract.functions.timeRemaining().call()
#         return {"remainingTimeInPhase": remaining_time}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/current_round")
# def get_current_round():
#     try:
#         round_num = contract.functions.currentRound().call()
#         return {"currentRound": round_num}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/current_phase")
# def get_current_phase():
#     try:
#         phase = contract.functions.currentPhase().call()
#         phase_mapping = {
#             0: "DataSubmission",
#             1: "Execution",
#             2: "Energy Transfering",
#             # add more if needed
#         }
#         phase_str = phase_mapping.get(phase, str(phase))
#         return {"currentPhase": phase_str}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/previous_hash")
# def get_previous_hash():
#     try:
#         phash = contract.functions.previousHash().call()
#         return {"previousHash": phash.hex() if isinstance(phash, bytes) else phash}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/previous_hash_execution")
# def get_previous_hash_execution():
#     try:
#         phash_exec = contract.functions.previousHashExecution().call()
#         return {"previousHashExecution": phash_exec.hex() if isinstance(phash_exec, bytes) else phash_exec}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/final_hash")
# def get_final_hash():
#     try:
#         fhash = contract.functions.finalHash().call()
#         return {"finalHash": fhash.hex() if isinstance(fhash, bytes) else fhash}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/submitted_results")
# def get_submitted_results():
#     try:
#         results = []
#         for i in range(5):
#             submitter, result_hash = contract.functions.submittedResults(i).call()
#             results.append({
#                 "submitter": submitter,
#                 "resultHash": result_hash.hex()  # convert bytes32 → hex string
#             })
#         return {"submittedResults": results}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/result_submission_count")
# def get_result_submission_count():
#     try:
#         count = contract.functions.resultSubmissionCount().call()
#         return {"resultSubmissionCount": count}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/has_submitted_result/{address}")
# def get_has_submitted_result(address: str):
#     try:
#         checksum_addr = Web3.to_checksum_address(address)
#         has_submitted = contract.functions.hasSubmittedResult(checksum_addr).call()
#         return {"address": checksum_addr, "hasSubmittedResult": has_submitted}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# @app.get("/bidding-results")
# def get_bidding_results():
#     data = load_bidding_results()

#     return {
#         "status": "success",
#         "total_matches": len(data),
#         "data": data
#     }


# @app.get("/keeper/status")
# def keeper_status():
#     """Check current phase, round and time remaining."""
#     try:
#         time_left     = contract.functions.timeRemaining().call()
#         current_phase = contract.functions.currentPhase().call()
#         current_round = contract.functions.currentRound().call()

#         phase_names = {0: "DataSubmission", 1: "Execution"}

#         return {
#             "status":        "running",
#             "currentRound":  current_round,
#             "currentPhase":  phase_names.get(current_phase, str(current_phase)),
#             "timeRemaining": time_left,
#             "willAdvanceIn": f"{time_left} seconds" if time_left > 0 else "advancing soon"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/keeper/force_advance")
# def keeper_force_advance():
#     """Manually force a phase advance (for testing or emergency use)."""
#     try:
#         old_phase = contract.functions.currentPhase().call()
#         old_round = contract.functions.currentRound().call()

#         receipt = send_transaction(contract.functions.advancePhase())

#         new_phase = contract.functions.currentPhase().call()
#         new_round = contract.functions.currentRound().call()

#         phase_names = {0: "DataSubmission", 1: "Execution"}

#         if receipt.status == 1:
#             return {
#                 "status":   "success",
#                 "before":   {"round": old_round, "phase": phase_names.get(old_phase)},
#                 "after":    {"round": new_round, "phase": phase_names.get(new_phase)},
#                 "txHash":   receipt.transactionHash.hex()
#             }
#         else:
#             raise HTTPException(status_code=400, detail="advancePhase transaction failed")

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# # ----------------------------- Transfer Energy  Controling Hardware and Relaying  -----------------------------------


# # def get_eth_address_from_ip(ip: str):
# #     hostname = ip
# #     if not hostname:
# #         raise Exception("Hostname not found")

# #     w3, _, sender_address, _ = get_web3_rpc(hostname)
# #     return sender_address


# # @app.get("/pi/address-from-ip/{ip}")
# # def address_from_ip(ip: str):
# #     try:
# #         address = get_eth_address_from_ip(ip)
# #         return {
# #             "ip": ip,
# #             "eth_address": address
# #         }
# #     except Exception as e:
# #         raise HTTPException(status_code=400, detail=str(e))



# # ─── Constants ────────────────────────────────────────────────────────────────







# """
# transfer_endpoint.py
# ────────────────────
# Drop-in addition to your existing main.py.

# Flow when POST /transfer is called:
#   1. Read result.json  →  list of {buyer_id, seller_id, energy_matched, price}
#   2. Map each Ethereum address → Pi IP using pis.json (eth_address field)
#   3. For every match:
#        - Call POST /transfer/start on SELLER Pi  (seller pushes energy out)
#        - Call POST /transfer/start on BUYER Pi   (buyer receives energy in)
#   4. Poll GET /transfer/status on BOTH Pis in parallel until both complete
#   5. All matches run in parallel via ThreadPoolExecutor
#   6. Return per-match summary with both seller and buyer status
# """






# # ─── Helpers ──────────────────────────────────────────────────────────────────

# def load_result_json(path: str = RESULT_FILE) -> List[Dict]:
#     with open(path, "r") as f:
#         return json.load(f)


# def build_address_to_pi_map(pis_json_path: str = PIS_JSON_PATH) -> Dict[str, Dict]:
#     with open(pis_json_path, "r") as f:
#         pis: Dict = json.load(f)

#     mapping = {}
#     for name, info in pis.items():
#         addr = info.get("eth_address", "").lower()
#         if addr:
#             mapping[addr] = {
#                 "name":       name,
#                 "hostname":   info["hostname"],
#                 "meter_port": info.get("meter_port", METER_API_PORT),
#             }
#     return mapping


# def meter_url(hostname: str, port: int) -> str:
#     return f"http://{hostname}:{port}"


# def pi_start_transfer(pi_info: Dict, from_hostname: str, to_hostname: str, energy_kwh: float, from_port: int, to_port: int) -> Dict:
#     """
#     Calls POST /transfer/start on the given Pi.
#     from_hostname = the Pi pushing energy (seller)
#     to_hostname   = the Pi receiving energy (buyer)
#     """
#     url = f"{meter_url(pi_info['hostname'], pi_info['meter_port'])}/transfer/start"
#     payload = {
#         "from_pi_ip":   from_hostname,
#         "to_pi_ip":     to_hostname,
#         "transfer_kwh": energy_kwh,
#         "from_port":   from_port,
#         "to_port":     to_port
#     }
#     resp = requests.post(url, json=payload, timeout=15)
#     resp.raise_for_status()
#     return resp.json()



# def pi_poll_transfer_status(pi_info: Dict, label: str) -> Dict:
#     url = f"{meter_url(pi_info['hostname'], pi_info['meter_port'])}/transfer/status"

#     retry_count = 0
#     MAX_RETRIES = 5

#     while True:
#         try:
#             resp = requests.get(url, timeout=10)
#             resp.raise_for_status()
#             status = resp.json()

#             # ✅ Normal completion
#             if not status.get("active", True):
#                 return status

#             print(f"[transfer/{label}] {pi_info['name']} active... "
#                   f"({status.get('current_energy_kwh')} / {status.get('threshold_kwh')} kWh)")

#             retry_count = 0  # reset on success

#         except requests.exceptions.Timeout:
#             retry_count += 1
#             print(f"[ERROR][{label}] Timeout contacting {pi_info['name']} (retry {retry_count})")

#         except requests.exceptions.ConnectionError:
#             retry_count += 1
#             print(f"[ERROR][{label}] Connection error with {pi_info['name']} (retry {retry_count})")

#         except requests.exceptions.HTTPError as e:
#             print(f"[ERROR][{label}] HTTP error from {pi_info['name']}: {e}")
#             return {
#                 "active": False,
#                 "relay_on": None,
#                 "stop_reason": "http_error",
#                 "error": str(e)
#             }

#         except Exception as e:
#             print(f"[ERROR][{label}] Unexpected error: {e}")
#             return {
#                 "active": False,
#                 "relay_on": None,
#                 "stop_reason": "unexpected_error",
#                 "error": str(e)
#             }

#         # ❌ If too many failures → stop polling (but DO NOT stop relay)
#         if retry_count >= MAX_RETRIES:
#             print(f"[CRITICAL][{label}] Max retries reached for {pi_info['name']}")

#             return {
#                 "active": False,
#                 "relay_on": None,
#                 "stop_reason": "connection_lost",
#                 "error": f"Lost connection to {pi_info['name']}"
#             }

#         time.sleep(TRANSFER_POLL_INTERVAL_S)


# # def pi_poll_transfer_status(
# #     pi_info: Dict,
# #     label: str,
# #     from_hostname: str,
# #     to_hostname: str,
# #     timeout_s: int = TRANSFER_TIMEOUT_S
# #    ) -> Dict:
# #     """
# #     Polls GET /transfer/status on a Pi until active == False or timeout.
# #     label = "seller" or "buyer" for logging.
# #     """
# #     url     = f"{meter_url(pi_info['hostname'], pi_info['meter_port'])}/transfer/status"
# #     elapsed = 0

# #     while elapsed < timeout_s:
# #         resp = requests.get(url, timeout=10)
# #         resp.raise_for_status()
# #         status = resp.json()

# #         if not status.get("active", True):
# #             return status

# #         print(f"[transfer/{label}] {pi_info['name']} active... "
# #               f"({status.get('current_energy_kwh')} / {status.get('threshold_kwh')} kWh)")

# #         time.sleep(TRANSFER_POLL_INTERVAL_S)
# #         elapsed += TRANSFER_POLL_INTERVAL_S

# #     # Timed out — gracefully stop
# #     # try:
# #     #     requests.post(
# #     #         f"{meter_url(pi_info['hostname'], pi_info['meter_port'])}/transfer/stop",
# #     #         json={
# #     #             "from_pi_ip":   pi_info["hostname"],
# #     #             "to_pi_ip":     "",
# #     #             "transfer_kwh": 0,
# #     #         },
# #     #         timeout=10,
# #     #     )
# #     # except Exception:
# #     #     pass

# #         try:
# #             verify = requests.get(
# #                 f"{meter_url(pi_info['hostname'], pi_info['meter_port'])}/transfer/status",
# #                 timeout=5
# #             ).json()

# #             if verify.get("relay_on"):
# #                 print(f"[CRITICAL] Relay still ON → forcing stop again")

# #                 requests.post(
# #                 f"{meter_url(pi_info['hostname'], pi_info['meter_port'])}/transfer/stop",
# #                 json={
# #                     "from_pi_ip": from_hostname,
# #                     "to_pi_ip": to_hostname,
# #                     "transfer_kwh": 0,
# #                 },
# #                 timeout=5,
# #                 )
# #         except Exception as e:
# #             print(f"[VERIFY ERROR] {e}")

# #     return {"active": False, "stop_reason": "timeout", "relay_on": False}


# def execute_single_match(match: Dict, addr_map: Dict) -> Dict:
#     """
#     Runs one buyer<->seller match end-to-end:
#       - Starts transfer on BOTH seller and buyer Pis simultaneously
#       - Polls BOTH statuses in parallel until both complete
#     """
#     buyer_addr  = match["buyer_id"].lower()
#     seller_addr = match["seller_id"].lower()
#     energy_kwh  = match["energy_matched"]
#     price       = match["price"]

#     result = {
#         "buyer":          match["buyer_id"],
#         "seller":         match["seller_id"],
#         "energy_kwh":     energy_kwh,
#         "price":          price,
#         "seller_status":  None,
#         "buyer_status":   None,
#         "error":          None,
#     }

#     # ── 1. Resolve Pi info ────────────────────────────────────────────────────
#     seller_info = addr_map.get(seller_addr)
#     buyer_info  = addr_map.get(buyer_addr)

#     if not seller_info:
#         result["error"] = f"Seller {match['seller_id']} not found in pis.json"
#         return result
#     if not buyer_info:
#         result["error"] = f"Buyer {match['buyer_id']} not found in pis.json"
#         return result

#     print(f"[transfer] {seller_info['name']} -> {buyer_info['name']}  "
#           f"{energy_kwh} kWh @ {price}")

#     # ── 2. Start transfer on BOTH Pis simultaneously ──────────────────────────
#     def start_seller():
#         return pi_start_transfer(
#             seller_info,
#             from_hostname=seller_info["hostname"],
#             to_hostname=buyer_info["hostname"],
#             energy_kwh=energy_kwh,
#             from_port=seller_info["meter_port"],
#             to_port=buyer_info["meter_port"]
#         )

#     def start_buyer():
#         return pi_start_transfer(
#             buyer_info,
#             from_hostname=seller_info["hostname"],
#             to_hostname=buyer_info["hostname"],
#             energy_kwh=energy_kwh,
#             from_port=seller_info["meter_port"],
#             to_port=buyer_info["meter_port"]
#         )

#     with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
#         seller_start_future = pool.submit(start_seller)
#         buyer_start_future  = pool.submit(start_buyer)

#         try:
#             seller_start = seller_start_future.result(timeout=20)
#             print(f"[transfer] seller started: {seller_start}")
#         except Exception as e:
#             result["error"] = f"Failed to start transfer on seller {seller_info['name']}: {e}"
#             # Cancel buyer too
#             try:
#                 requests.post(
#                     f"{meter_url(buyer_info['hostname'], buyer_info['meter_port'])}/transfer/stop",
#                     json={"from_pi_ip": seller_info["hostname"],
#                           "to_pi_ip": buyer_info["hostname"], "transfer_kwh": 0},
#                     timeout=10,
#                 )
#             except Exception:
#                 pass
#             return result

#         try:
#             buyer_start = buyer_start_future.result(timeout=20)
#             print(f"[transfer] buyer started: {buyer_start}")
#         except Exception as e:
#             result["error"] = f"Failed to start transfer on buyer {buyer_info['name']}: {e}"
#             # Cancel seller too
#             try:
#                 requests.post(
#                     f"{meter_url(seller_info['hostname'], seller_info['meter_port'])}/transfer/stop",
#                     json={"from_pi_ip": seller_info["hostname"],
#                           "to_pi_ip": buyer_info["hostname"], "transfer_kwh": 0},
#                     timeout=10,
#                 )
#             except Exception:
#                 pass
#             return result

#     # ── 3. Poll BOTH Pis in parallel until both complete ──────────────────────
#     with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
#         seller_poll = pool.submit(pi_poll_transfer_status, seller_info, "seller")
#         buyer_poll  = pool.submit(pi_poll_transfer_status, buyer_info,  "buyer")
#         # seller_poll = pool.submit(
#         #     pi_poll_transfer_status,
#         #     seller_info,
#         #     "seller",
#         #     seller_info["hostname"],   # from
#         #     buyer_info["hostname"]     # to
#         # )

#         # buyer_poll = pool.submit(
#         #     pi_poll_transfer_status,
#         #     buyer_info,
#         #     "buyer",
#         #     seller_info["hostname"],   # from
#         #     buyer_info["hostname"]     # to
#         # )

#         try:
#             result["seller_status"] = seller_poll.result()
#         except Exception as e:
#             result["seller_status"] = {"error": str(e)}

#         try:
#             result["buyer_status"] = buyer_poll.result()
#         except Exception as e:
#             result["buyer_status"] = {"error": str(e)}

#     seller_reason = result.get("seller_status", {}).get("stop_reason", "completed")
#     buyer_reason  = result.get("buyer_status",  {}).get("stop_reason", "completed")
#     print(f"[transfer] complete — seller: {seller_reason}, buyer: {buyer_reason}")

#     return result


# # ─── Endpoints ────────────────────────────────────────────────────────────────

# @app.post("/transfer")
# def transfer_energy():
#     """
#     Reads result.json and executes all energy transfers in parallel.
#     For each match:
#       - Opens relay on both seller Pi and buyer Pi
#       - Polls both until energy transfer completes
#       - Returns status from both sides
#     """
#     try:
#         matches = load_result_json(RESULT_FILE)
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail=f"{RESULT_FILE} not found")
#     except json.JSONDecodeError as e:
#         raise HTTPException(status_code=400, detail=f"Invalid JSON in {RESULT_FILE}: {e}")

#     if not matches:
#         return {"status": "no_matches", "results": []}

#     try:
#         addr_map = build_address_to_pi_map(PIS_JSON_PATH)

#         print("=== ADDRESS MAP ===")
#         for addr, info in addr_map.items():
#             print(f"  {addr} -> {info['name']} @ {info['hostname']}:{info['meter_port']}")

#         matches = load_result_json(RESULT_FILE)
#         print("=== MATCHES ===")
#         for m in matches:
#             print(f"  buyer:  {m['buyer_id'].lower()}")
#             print(f"  seller: {m['seller_id'].lower()}")

#     except FileNotFoundError:
#         raise HTTPException(status_code=500, detail="pis.json not found")

#     results: List[Dict[str, Any]] = []

#     with concurrent.futures.ThreadPoolExecutor(max_workers=len(matches)) as pool:
#         futures = {
#             pool.submit(execute_single_match, match, addr_map): match
#             for match in matches
#         }
#         for future in concurrent.futures.as_completed(futures):
#             try:
#                 results.append(future.result())
#             except Exception as e:
#                 original = futures[future]
#                 results.append({
#                     "buyer":  original.get("buyer_id"),
#                     "seller": original.get("seller_id"),
#                     "error":  str(e),
#                 })

#     success_count = sum(
#     1 for r in results
#     if r.get("error") is None
#     and r.get("seller_status", {}).get("stop_reason") == "THRESHOLD_REACHED"
#     and r.get("buyer_status", {}).get("stop_reason") == "THRESHOLD_REACHED"
#     )

#     return {
#         "status":        "completed",
#         "total_matches": len(matches),
#         "succeeded":     success_count,
#         "failed":        len(matches) - success_count,
#         "results":       results,
#     }


# @app.get("/transfer/status/{hostname}")
# def get_transfer_status_for_pi(hostname: str):
#     """
#     Proxy GET /transfer/status from any Pi by hostname/IP.
#     Works for both seller and buyer Pis.
#     """
#     try:
#         with open(PIS_JSON_PATH) as f:
#             pis = json.load(f)

#         port = METER_API_PORT
#         for info in pis.values():
#             if info.get("hostname") == hostname:
#                 port = info.get("meter_port", METER_API_PORT)
#                 break

#         resp = requests.get(f"http://{hostname}:{port}/transfer/status", timeout=10)
#         resp.raise_for_status()
#         return resp.json()

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# if __name__ == "__main__":
    
#     import uvicorn
#     import webbrowser

#     local_ip = get_local_ip()
#     print("\n🚀 P2P Energy Trading API running!")
#     print(f"   → Local Access:   http://localhost:8000")
#     print(f"   → Network Access: http://{local_ip}:8000\n")

#     # Optional: open in browser (comment out if not desired)
#     # webbrowser.open(f"http://{local_ip}:8000")

#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",  # allows both localhost and network access
#         port=8000,
#         reload=True
#     )






#source ../../pi-venv/bin/activate
from multiprocessing import pool
import subprocess
from eth_account import Account
import os, time
import json
from web3 import Web3
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
import requests
import atexit
import threading
from contextlib import asynccontextmanager
import concurrent.futures
from typing import List, Dict, Any
from collections import defaultdict
from eth_utils import to_checksum_address

MATCH_FILE = "matching_result.json"

load_dotenv()


def load_matches():
    with open(MATCH_FILE) as f:
        return json.load(f)


PI_NODES = [
    {"name": "pi_2",  "host": "100.93.80.36",    "username": "pi", "password": "Lums12345", "port": 8002},
    {"name": "pi_3",  "host": "100.71.238.87",   "username": "pi", "password": "Lums12345", "port": 8003},
    {"name": "pi_4",  "host": "100.80.205.106",  "username": "pi", "password": "Lums12345", "port": 8004},
    {"name": "pi_11", "host": "100.120.139.128", "username": "pi", "password": "Lums12345", "port": 8005},
    {"name": "pi_13", "host": "100.80.11.48",    "username": "pi", "password": "Lums12345", "port": 8006},
    {"name": "pi_15", "host": "100.120.124.29",  "username": "pi", "password": "Lums12345", "port": 8007},
]

ROLE_MAP = {
    "buyer":  1,
    "seller": 2
}

SCALING_FACTOR = 1000

PI_PROJECT_DIR   = "/home/pi/Desktop/P2PET_Dynamic/P2PET"
PI_VENV_ACTIVATE = f"source {PI_PROJECT_DIR}/venv/bin/activate"
PI_API_DIR       = f"{PI_PROJECT_DIR}/p2p-energy-trading-contract/api"

with open("NodeNum.txt", "r") as f:
    node_number = int(f.read().strip())

rpc_port_num = 22000
RPC_URL = f"http://{'100.71.238.87'}:{str(rpc_port_num + node_number)}"

CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")
ABI_PATH              = os.getenv("ABI_PATH")

keystore = subprocess.check_output(
    "cd ..; cd ..; cd quorum-ibft-chain; cd node*; cd data/keystore; cat $(ls | head -n 1)",
    shell=True,
    text=True,
).strip()

ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")
PI_PASSWORD      = "Lums12345"

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

w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

account        = w3.eth.account.from_key(PRIVATE_KEY)
sender_address = account.address

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

RESULT_FILE              = "match_result.json"
PIS_JSON_PATH            = "pis.json"
METER_API_PORT           = 8002
TRANSFER_POLL_INTERVAL_S = 2
TRANSFER_TIMEOUT_S       = 300

# ─── Single PHASE_NAMES definition (was duplicated before — caused the bug) ───
PHASE_NAMES = {
    0: "DataSubmission",
    1: "Execution",
    2: "EnergyTransfer",
}

# ─── Transfer window tracking ─────────────────────────────────────────────────
transfer_deadlines: dict[int, float] = {}
transfer_deadlines_lock = threading.Lock()
TRANSFER_WINDOW_SECONDS = 60 * 60  # 60 minutes


# ─── Pi startup ───────────────────────────────────────────────────────────────

def start_pi(node: dict) -> bool:
    name, host, username, password, port = (
        node["name"], node["host"], node["username"], node["password"], node["port"]
    )
    print(f"[{name}] Connecting to {host} ...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"[{name}] ❌ SSH failed: {e}")
        return False

    _, stdout, _ = client.exec_command(f"fuser -k {port}/tcp 2>/dev/null || true")
    stdout.channel.recv_exit_status()
    time.sleep(0.5)

    start_cmd = (
        f"cd {PI_API_DIR} && "
        f"{PI_VENV_ACTIVATE} && "
        f"nohup python meter_api.py --port {port} > meter_{port}.log 2>&1 &"
    )
    _, stdout, _ = client.exec_command(start_cmd)
    stdout.channel.recv_exit_status()
    time.sleep(3)

    _, stdout, _ = client.exec_command("pgrep -fa meter_api.py")
    running = bool(stdout.read().decode().strip())
    client.close()

    if running:
        print(f"[{name}] ✅  http://{host}:{port}")
    else:
        print(f"[{name}] ❌ Process did not start")
    return running


def start_all_pis():
    print("\n🚀 Starting meter_api.py on all Pi nodes...")
    for node in PI_NODES:
        start_pi(node)
    print("✅ Pi startup sequence complete.\n")


# ─── Formatting helpers ───────────────────────────────────────────────────────

def _fmt(seconds) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def _ts(unix_ts: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(unix_ts))


# ─── Transfer window helpers ──────────────────────────────────────────────────

def is_transfer_window_open(round_number: int) -> bool:
    return get_transfer_window_remaining(round_number) > 0


def get_transfer_window_remaining(round_number: int) -> float:
    with transfer_deadlines_lock:
        deadline = transfer_deadlines.get(round_number)
    if deadline is None:
        return 0.0
    return max(0.0, deadline - time.time())


def _report_open_windows(current_round: int):
    now = time.time()
    with transfer_deadlines_lock:
        all_deadlines  = dict(transfer_deadlines)
        open_windows   = [(rnd, dl) for rnd, dl in transfer_deadlines.items() if dl > now]

    if not all_deadlines:
        print("[Keeper]    No transfer windows tracked yet.")
        return

    if not open_windows:
        print(f"[Keeper]    Tracked rounds: {list(all_deadlines.keys())} — all closed.")
        return

    for rnd, deadline in sorted(open_windows):
        remaining = deadline - now
        if rnd < current_round:
            tag = f" 🔁 overlap — {_fmt(remaining)} left before closing"
        elif rnd == current_round:
            tag = f" ✅ active — {_fmt(remaining)} remaining"
        else:
            tag = f" ⏳ pending — {_fmt(remaining)} remaining"
        print(f"[Keeper] 🔋 Round {rnd} transfer window:{tag} (closes {_ts(deadline)})")


# ─── Auto transfer trigger ────────────────────────────────────────────────────

# def _auto_trigger_transfer(round_number: int):
#     """
#     Called in a background thread when EnergyTransfer phase starts.
#     Calls transfer_energy() directly — no HTTP, no connection issues.
#     """
#     MAX_RETRIES   = 3
#     RETRY_DELAY   = 5
#     INITIAL_DELAY = 3

#     print(f"[AutoTransfer] 🚀 Round {round_number} — starting in {INITIAL_DELAY}s...")
#     time.sleep(INITIAL_DELAY)

#     for attempt in range(1, MAX_RETRIES + 1):
#         try:
#             print(f"[AutoTransfer] 🔄 Attempt {attempt}/{MAX_RETRIES} — calling transfer_energy()...")

#             result    = transfer_energy()
#             total     = result.get("total_matches", 0)
#             succeeded = result.get("succeeded", 0)
#             failed    = result.get("failed", 0)

#             print(
#                 f"[AutoTransfer] ✅ Round {round_number} transfer complete!"
#                 f"\n               Total: {total} | Succeeded: {succeeded} | Failed: {failed}"
#             )

#             for r in result.get("results", []):
#                 error         = r.get("error")
#                 seller_status = r.get("seller_status") or {}
#                 buyer_status  = r.get("buyer_status")  or {}
#                 seller_reason = seller_status.get("stop_reason", "no_status")
#                 buyer_reason  = buyer_status.get("stop_reason",  "no_status")
#                 seller_error  = seller_status.get("error")
#                 buyer_error   = buyer_status.get("error")

#                 if error:
#                     print(f"[AutoTransfer]   ❌ {r.get('seller')} → {r.get('buyer')}: {error}")
#                 else:
#                     success = (
#                         seller_reason == "THRESHOLD_REACHED"
#                         and buyer_reason == "THRESHOLD_REACHED"
#                     )
#                     print(
#                         f"[AutoTransfer]   {'✅' if success else '⚠️ '} "
#                         f"{r.get('seller')} → {r.get('buyer')} | "
#                         f"energy: {r.get('energy_kwh')} kWh | "
#                         f"seller: {seller_reason} | buyer: {buyer_reason}"
#                     )
#                     if seller_error:
#                         print(f"[AutoTransfer]      seller error: {seller_error}")
#                     if buyer_error:
#                         print(f"[AutoTransfer]      buyer error:  {buyer_error}")

#             return  # ✅ success — stop retrying

#         except FileNotFoundError as e:
#             print(f"[AutoTransfer] ⚠️  Attempt {attempt}/{MAX_RETRIES} — file not ready: {e}")

#         except Exception as e:
#             print(f"[AutoTransfer] ❌ Attempt {attempt}/{MAX_RETRIES} — error: {e}")

#         if attempt < MAX_RETRIES:
#             print(f"[AutoTransfer] 🔁 Retrying in {RETRY_DELAY}s...")
#             time.sleep(RETRY_DELAY)

#     print(f"[AutoTransfer] ❌ Round {round_number} — all {MAX_RETRIES} attempts failed.")

def _auto_trigger_transfer(round_number: int):
    """
    Keeps retrying transfer_energy() until ALL matches succeed (THRESHOLD_REACHED)
    or the transfer window closes — whichever comes first.
    """
    RETRY_DELAY   = 10  # seconds between retries
    INITIAL_DELAY = 3   # give match_result.json a moment to be ready

    print(f"[AutoTransfer] 🚀 Round {round_number} — starting in {INITIAL_DELAY}s...")
    time.sleep(INITIAL_DELAY)

    attempt = 0

    while True:
        # ── Stop if transfer window has closed ────────────────────────────
        remaining = get_transfer_window_remaining(round_number)
        if remaining <= 0:
            print(f"[AutoTransfer] ⏰ Round {round_number} — transfer window closed. Stopping.")
            return

        attempt += 1
        print(
            f"\n[AutoTransfer] 🔄 Attempt {attempt} — "
            f"Round {round_number} | Window: {_fmt(remaining)} remaining"
        )

        try:
            result    = transfer_energy()
            total     = result.get("total_matches", 0)
            succeeded = result.get("succeeded", 0)
            failed    = result.get("failed", 0)

            print(
                f"[AutoTransfer] 📊 Round {round_number} attempt {attempt} result: "
                f"Total={total} | Succeeded={succeeded} | Failed={failed}"
            )

            # ── Log per-match detail ──────────────────────────────────────
            all_success = True
            for r in result.get("results", []):
                error         = r.get("error")
                seller_status = r.get("seller_status") or {}
                buyer_status  = r.get("buyer_status")  or {}
                seller_reason = seller_status.get("stop_reason", "no_status")
                buyer_reason  = buyer_status.get("stop_reason",  "no_status")
                seller_error  = seller_status.get("error")
                buyer_error   = buyer_status.get("error")

                match_success = (
                    error is None
                    and seller_reason == "THRESHOLD_REACHED"
                    and buyer_reason  == "THRESHOLD_REACHED"
                )

                if not match_success:
                    all_success = False

                icon = "✅" if match_success else "❌"
                print(
                    f"[AutoTransfer]   {icon} "
                    f"{r.get('seller')} → {r.get('buyer')} | "
                    f"energy: {r.get('energy_kwh')} kWh | "
                    f"seller: {seller_reason} | buyer: {buyer_reason}"
                )
                if error:
                    print(f"[AutoTransfer]      match error:  {error}")
                if seller_error:
                    print(f"[AutoTransfer]      seller error: {seller_error}")
                if buyer_error:
                    print(f"[AutoTransfer]      buyer error:  {buyer_error}")

            # ── All matches succeeded — done ──────────────────────────────
            if all_success and total > 0:
                print(f"[AutoTransfer] ✅ Round {round_number} — all {total} transfers completed successfully!")
                return

            # ── Some failed — check window and retry ──────────────────────
            remaining = get_transfer_window_remaining(round_number)
            if remaining <= 0:
                print(f"[AutoTransfer] ⏰ Round {round_number} — window closed after attempt {attempt}. Stopping.")
                return

            print(
                f"[AutoTransfer] ⚠️  {failed}/{total} failed — "
                f"retrying in {RETRY_DELAY}s ({_fmt(remaining)} left in window)..."
            )

        except FileNotFoundError as e:
            remaining = get_transfer_window_remaining(round_number)
            print(
                f"[AutoTransfer] ⚠️  Attempt {attempt} — match file not ready: {e} | "
                f"retrying in {RETRY_DELAY}s ({_fmt(remaining)} left)..."
            )
            if remaining <= 0:
                print(f"[AutoTransfer] ⏰ Window closed. Stopping.")
                return

        except Exception as e:
            remaining = get_transfer_window_remaining(round_number)
            print(
                f"[AutoTransfer] ❌ Attempt {attempt} — error: {e} | "
                f"retrying in {RETRY_DELAY}s ({_fmt(remaining)} left)..."
            )
            if remaining <= 0:
                print(f"[AutoTransfer] ⏰ Window closed. Stopping.")
                return

        time.sleep(RETRY_DELAY)


# ─── Phase Keeper Bot ─────────────────────────────────────────────────────────

def phase_keeper_loop():
    """
    Round structure (60 min total):
        T+00  DataSubmission  (10 min)
        T+10  Execution       (10 min)
        T+20  EnergyTransfer  (40 min on-chain)  ← 60-min transfer window opens here
        T+60  Round N+1 starts                   ← window still open (20 min left)
        T+80  Round N+1 EnergyTransfer starts    ← Round N window closes
    """
    print("⏰ Phase keeper bot started.")
    print("   DataSubmission(10m) → Execution(10m) → EnergyTransfer(40m) = 60 min round")
    print("   Transfer window = 60 min (overlaps 20 min into next round)\n")

    FAST_POLL_THRESHOLD  = 60
    FAST_POLL_INTERVAL   = 2
    NORMAL_POLL_INTERVAL = 30

    # ── Recovery: rebuild deadline if we restart mid-EnergyTransfer ──────────
    try:
        current_phase = contract.functions.currentPhase().call()
        current_round = contract.functions.currentRound().call()
        if current_phase == 2:
            remaining_onchain = contract.functions.transferWindowRemaining(current_round).call()
            if remaining_onchain > 0:
                deadline = time.time() + remaining_onchain
                with transfer_deadlines_lock:
                    transfer_deadlines[current_round] = deadline
                print(
                    f"[Keeper] 🔄 Recovered Round {current_round} transfer window — "
                    f"{_fmt(remaining_onchain)} remaining (closes {_ts(deadline)})"
                )
            else:
                print(f"[Keeper] ℹ️  Round {current_round} is EnergyTransfer but window already closed.")
        else:
            print(f"[Keeper] ℹ️  Started in phase {PHASE_NAMES.get(current_phase)} — no recovery needed.")
    except Exception as e:
        print(f"[Keeper] ⚠️  Recovery check failed: {e}")

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        try:
            time_left     = contract.functions.timeRemaining().call()
            round_left    = contract.functions.roundTimeRemaining().call()
            current_phase = contract.functions.currentPhase().call()
            current_round = contract.functions.currentRound().call()

            print(
                f"\n[Keeper] Round {current_round} | {PHASE_NAMES.get(current_phase, str(current_phase))}"
                f"\n         Phase left: {_fmt(time_left)} | Round left: {_fmt(round_left)}"
            )

            _report_open_windows(current_round)

            if time_left == 0:
                print(f"[Keeper] ⏰ Phase timer expired — advancing...")
                receipt = send_transaction(contract.functions.advancePhase())

                if receipt.status == 1:
                    new_phase = contract.functions.currentPhase().call()
                    new_round = contract.functions.currentRound().call()

                    if new_round > current_round:
                        print(f"[Keeper] 🔄 Round {current_round} complete → Round {new_round} started!")

                    print(f"[Keeper] ✅ Now: Round {new_round} | {PHASE_NAMES.get(new_phase, str(new_phase))}")

                    if new_phase == 2:
                        # ── open 60-min transfer window for the round that just finished Execution
                        deadline = time.time() + TRANSFER_WINDOW_SECONDS
                        with transfer_deadlines_lock:
                            transfer_deadlines[current_round] = deadline

                        # verify stored
                        with transfer_deadlines_lock:
                            stored = transfer_deadlines.get(current_round)

                        print(
                            f"[Keeper] 🔋 Round {current_round} transfer window opened!"
                            f"\n         Deadline stored: {stored is not None} | "
                            f"Closes at {_ts(deadline)} — "
                            f"20 min overlap into Round {current_round + 1}"
                        )
                        print(f"[Keeper]    All tracked deadlines: { {k: _ts(v) for k, v in transfer_deadlines.items()} }")

                        # auto-trigger transfer directly (no HTTP)
                        transfer_thread = threading.Thread(
                            target=_auto_trigger_transfer,
                            args=(current_round,),
                            daemon=True
                        )
                        transfer_thread.start()

                    elif new_phase == 0:
                        prev = new_round - 1
                        remaining = get_transfer_window_remaining(prev)
                        if remaining > 0:
                            print(
                                f"[Keeper] ⚠️  Round {prev} transfer window still open! "
                                f"{_fmt(remaining)} remaining (overlap period)"
                            )
                        print(f"[Keeper] 📋 Round {new_round} DataSubmission open.")

                    elif new_phase == 1:
                        prev = new_round - 1
                        remaining = get_transfer_window_remaining(prev)
                        if remaining > 0:
                            print(
                                f"[Keeper] ⚠️  Round {prev} transfer window still open! "
                                f"{_fmt(remaining)} remaining — closes when this Execution ends"
                            )
                        print(f"[Keeper] ⚙️  Round {new_round} Execution open.")

                else:
                    print("[Keeper] ❌ advancePhase() transaction failed.")

                sleep_time = NORMAL_POLL_INTERVAL

            elif time_left <= FAST_POLL_THRESHOLD:
                print(f"[Keeper] ⚡ {time_left}s left — fast polling ({FAST_POLL_INTERVAL}s)")
                sleep_time = FAST_POLL_INTERVAL

            else:
                sleep_time = NORMAL_POLL_INTERVAL

        except Exception as e:
            print(f"[Keeper] ❌ Error: {e}")
            sleep_time = NORMAL_POLL_INTERVAL

        time.sleep(sleep_time)


# ─── App lifespan ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    pi_thread = threading.Thread(target=start_all_pis, daemon=True)
    pi_thread.start()

    keeper_thread = threading.Thread(target=phase_keeper_loop, daemon=True)
    keeper_thread.start()

    yield


app = FastAPI(title="P2P Energy Trading API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


def load_bidding_results():
    if not os.path.exists(RESULT_FILE):
        return []
    with open(RESULT_FILE, "r") as file:
        data = json.load(file)
    return data


def get_pi_hostname(host, file_path='pis.json'):
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


def get_dynamic_private_key(node_number,
                             base_dir="/home/pi/Desktop/P2PET_Dynamic/P2PET/quorum-ibft-chain",
                             account_password=ACCOUNT_PASSWORD,
                             remote_host=None,
                             remote_user="pi",
                             remote_password=PI_PASSWORD):
    try:
        node_path = Path(base_dir) / f"node{node_number}" / "data" / "keystore"

        if remote_host:
            print(f"🔄 Fetching keystore from remote Pi: {remote_host}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(remote_host, username=remote_user, password=remote_password)

            stdin, stdout, stderr = ssh.exec_command(f"ls {node_path} | head -n 1")
            keystore_filename = stdout.read().decode().strip()
            if not keystore_filename:
                raise FileNotFoundError(f"No keystore file found at {node_path}")

            stdin, stdout, stderr = ssh.exec_command(f"cat {node_path}/{keystore_filename}")
            keystore_content = stdout.read().decode()
            ssh.close()
        else:
            keystore_files = list(node_path.glob("*"))
            if not keystore_files:
                raise FileNotFoundError(f"No keystore files found in {node_path}")
            with open(keystore_files[0], "r") as f:
                keystore_content = f.read()

        private_key_bytes = Account.decrypt(keystore_content, account_password)
        private_key_hex   = private_key_bytes.hex()
        print(f"✅ Successfully decrypted private key for node{node_number}")
        return private_key_hex

    except Exception as e:
        raise RuntimeError(f"Failed to get private key for node {node_number}: {e}")


def get_web3_rpc(hostname, pis_json_path="pis.json"):
    try:
        with open(pis_json_path, "r") as f:
            pis_data = json.load(f)

        if hostname not in pis_data:
            raise HTTPException(status_code=404, detail=f"Hostname {hostname} not found in pis.json")

        node_info     = pis_data[hostname]
        node_number   = node_info["node_num"]
        node_hostname = node_info["hostname"]

        RPC_URL = f"http://{node_hostname}:{rpc_port_num + node_number}"
        print(f"Connecting to RPC: {RPC_URL}")

        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        if not w3.is_connected():
            raise Exception(f"Cannot connect to {RPC_URL}")

        dynamic_private_key = get_dynamic_private_key(node_number, remote_host=node_hostname)
        account        = w3.eth.account.from_key(dynamic_private_key)
        sender_address = account.address

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=abi
        )

        print(f"Connected successfully to node {node_number} ({hostname})")
        return w3, contract, sender_address, dynamic_private_key

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pis.json file not found")
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Missing key in pis.json: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing Web3: {e}")


def send_transaction(function_call):
    nonce = w3.eth.get_transaction_count(sender_address)
    tx = function_call.build_transaction({
        'from':     sender_address,
        'nonce':    nonce,
        'gas':      500000,
        'gasPrice': 0
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash   = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()} — waiting for receipt...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        print("Transaction failed.")
        try:
            tx_call = {'to': tx['to'], 'from': sender_address, 'data': tx['data'], 'gas': tx['gas']}
            w3.eth.call(tx_call, block_identifier=receipt.blockNumber)
            print("Unknown failure reason.")
        except ContractLogicError as e:
            message = str(e)
            if message.startswith("execution reverted:"):
                print(f"Revert reason: {message.split('execution reverted:')[1].strip()}")
            else:
                print(f"Revert reason: {message}")
        except Exception as e:
            print(f"Failed to decode revert reason: {e}")

    return receipt


def send_transaction_dynamic(w3, sender_address, function_call, dynamic_private_key):
    revert_reason = None
    try:
        nonce = w3.eth.get_transaction_count(sender_address)
        tx = function_call.build_transaction({
            'from':     sender_address,
            'nonce':    nonce,
            'gas':      500000,
            'gasPrice': 0
        })
        signed_tx = w3.eth.account.sign_transaction(tx, dynamic_private_key)
        tx_hash   = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Transaction sent: {tx_hash.hex()} — waiting for receipt...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 0:
            print("Transaction failed.")
            try:
                tx_call = {'to': tx['to'], 'from': sender_address, 'data': tx['data'], 'gas': tx['gas']}
                w3.eth.call(tx_call, block_identifier=receipt.blockNumber)
            except ContractLogicError as e:
                message = str(e)
                if message.startswith("execution reverted:"):
                    revert_reason = message.split("execution reverted:")[1].strip()
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


# ─── Basic endpoints ──────────────────────────────────────────────────────────

@app.get('/')
def root():
    return {"health": "ok", "status": True, "version": "2.0.0",
            "description": "This is P2P Energy trading contract api (Endpoints)"}


print("Contract Address:", CONTRACT_ADDRESS)


@app.get('/contract')
def get_contract():
    try:
        return {"contractAddress": CONTRACT_ADDRESS, "status": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/private-key')
def get_private_key():
    try:
        return {"Private Keys": PRIVATE_KEY, "status": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/dynamic_private-key/{hostname}')
def dynamic_key(hostname: str):
    try:
        _, _, _, dynamic_private_key = get_web3_rpc(hostname)
        return {"Dynamic Private Key": dynamic_private_key, "status": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Transfer window endpoint ─────────────────────────────────────────────────

@app.get("/transfer/window/remaining")
def get_transfer_window_remaining_endpoint():
    """
    Returns remaining transfer window time automatically based on current round/phase.
    - Round 1, Phase 0 or 1  → not started yet
    - Round 1, Phase 2       → Round 1 window running
    - Round 2, Phase 0 or 1  → Round 1 window overlap
    - Round 2, Phase 2       → Round 2 window running
    """
    try:
        current_round = contract.functions.currentRound().call()
        current_phase = contract.functions.currentPhase().call()
        phase_names   = {0: "DataSubmission", 1: "Execution", 2: "EnergyTransfer"}

        if current_round == 1 and current_phase in (0, 1):
            return {
                "status":             "not_started",
                "message":            "Transfer window has not opened yet. Waiting for Round 1 Execution to complete.",
                "currentRound":       current_round,
                "currentPhase":       phase_names[current_phase],
                "isOpen":             False,
                "remainingSeconds":   0,
                "remainingFormatted": "00:00",
                "transferRound":      None,
            }

        target_round = current_round if current_phase == 2 else current_round - 1

        remaining_onchain  = contract.functions.transferWindowRemaining(target_round).call()
        remaining_offchain = get_transfer_window_remaining(target_round)
        remaining          = max(int(remaining_onchain), int(remaining_offchain))
        is_open            = remaining > 0

        return {
            "status":             "open" if is_open else "closed",
            "message":            (
                f"Round {target_round} transfer window {'is open' if is_open else 'has closed'}."
                + (f" Overlapping into Round {current_round}." if target_round < current_round and is_open else "")
            ),
            "currentRound":       current_round,
            "currentPhase":       phase_names[current_phase],
            "isOpen":             is_open,
            "transferRound":      target_round,
            "remainingSeconds":   remaining,
            "remainingFormatted": _fmt(remaining),
            "closesAt":           _ts(time.time() + remaining) if remaining > 0 else "closed",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Registration ─────────────────────────────────────────────────────────────

@app.post("/dynamic_register")
def register_participant(hostname: str):
    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, contract.functions.register(), dynamic_private_key
        )
        if receipt.status == 1:
            return {"status": "success", "txHash": receipt.transactionHash.hex()}
        else:
            raise HTTPException(status_code=400, detail={"status": "failed", "reason": revert_reason or "Transaction reverted."})
    except HTTPException:
        raise
    except Exception as e:
        revert_reason = str(e)
        if "execution reverted" in revert_reason:
            revert_reason = revert_reason[revert_reason.find("execution reverted"):]
        raise HTTPException(status_code=400, detail={"status": "failed", "reason": revert_reason})


@app.post("/register")
def register_participant_simple():
    receipt = send_transaction(contract.functions.register())
    if receipt.status == 1:
        return {"status": "success", "message": "Transaction successful."}
    else:
        raise HTTPException(status_code=400, detail="Transaction failed.")


# ─── Submit data ──────────────────────────────────────────────────────────────

@app.post("/submit-data")
def submit_data_simple(role: int, energy: int, price: int):
    receipt = send_transaction(contract.functions.submitData(role, energy, price))
    if receipt.status == 1:
        return {"status": "success", "message": "Transaction successful."}
    else:
        raise HTTPException(status_code=400, detail="Transaction failed.")


def scale(value):
    return int(float(value) * SCALING_FACTOR)


@app.post("/dynamic_submit_data")
def submit_data(hostname: str, role: str, energy: float, price: float):
    role_normalized = role.strip().lower()
    if role_normalized not in ROLE_MAP:
        raise HTTPException(status_code=400, detail="Invalid role")

    role_int       = ROLE_MAP[role_normalized]
    energy_scaled  = scale(energy)
    price_scaled   = scale(price)

    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address,
            contract.functions.submitData(role_int, energy_scaled, price_scaled),
            dynamic_private_key
        )
        if receipt.status == 1:
            return {"status": "success", "message": "Transaction successful.", "txHash": receipt.transactionHash.hex()}
        else:
            raise HTTPException(status_code=400, detail={
                "status": "failed",
                "reason": revert_reason or "Transaction reverted.",
                "txHash": receipt.transactionHash.hex() if receipt else None,
            })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})


# ─── Hash participants ────────────────────────────────────────────────────────

@app.post("/Dynamic_hash_participants")
def hash_participants(hostname: str):
    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, contract.functions.hashParticipantsList(), dynamic_private_key
        )
        latest_hash = contract.functions.previousHash().call()

        if receipt.status == 1:
            return {
                "status":       "success",
                "message":      "✅ Hash calculated and submitted successfully.",
                "computedHash": latest_hash.hex(),
                "txHash":       receipt.transactionHash.hex()
            }
        else:
            raise HTTPException(status_code=400, detail={"reason": revert_reason or "Transaction failed."})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# ─── Advance phase ────────────────────────────────────────────────────────────

@app.post("/dynamic_advance_phase")
def advance_phase(hostname: str):
    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, contract.functions.advancePhase(), dynamic_private_key
        )
        current_phase = contract.functions.currentPhase().call()
        current_round = contract.functions.currentRound().call()
        phase_name    = PHASE_NAMES.get(current_phase, f"Unknown({current_phase})")

        if receipt.status == 1:
            return {
                "status": "success", "message": "Phase advanced successfully.",
                "currentRound": current_round, "phaseName": phase_name,
                "txHash": receipt.transactionHash.hex(), "revert_reason": revert_reason
            }
        else:
            return {
                "status": "failed", "message": "Transaction failed.",
                "currentRound": current_round, "phaseName": phase_name,
                "txHash": receipt.transactionHash.hex(),
                "revert_reason": revert_reason or "Transaction failed without revert reason"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Execution result ─────────────────────────────────────────────────────────

@app.post("/dynamic_submit_execution_result")
def dynamic_submit_execution_result(hostname: str):
    try:
        w3, contract, sender_address, dynamic_private_key = get_web3_rpc(hostname)
        participant_count, result_hash_hex = run_matching_and_get_hash(contract)
        hash_bytes32 = Web3.to_bytes(hexstr="0x" + result_hash_hex)

        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address,
            contract.functions.submitExecutionResult(hash_bytes32),
            dynamic_private_key
        )
        print("Participant Count:", participant_count)

        if receipt.status == 1:
            return {
                "status": "success", "participants": participant_count,
                "result_hash": f"0x{result_hash_hex}", "txHash": receipt.transactionHash.hex(),
                "revert_reason": revert_reason
            }
        else:
            return {
                "status": "failed", "participants": participant_count,
                "result_hash": f"0x{result_hash_hex}", "txHash": receipt.transactionHash.hex(),
                "revert_reason": revert_reason or "Transaction failed without revert reason"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Verify execution ─────────────────────────────────────────────────────────

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
        majority_hash, is_verified = contract.functions.verifyExecutionResult().call({'from': sender_address})
        receipt, revert_reason = send_transaction_dynamic(
            w3, sender_address, contract.functions.verifyExecutionResult(), dynamic_private_key
        )
        if receipt.status == 1:
            return {
                "status": "success", "message": "Execution verified successfully.",
                "txHash": receipt.transactionHash.hex(),
                "majority_hash": majority_hash.hex(), "is_verified": is_verified,
                "revert_reason": revert_reason
            }
        else:
            return {
                "status": "failed", "message": "Transaction failed.",
                "txHash": receipt.transactionHash.hex(),
                "revert_reason": revert_reason or "Transaction failed without revert reason"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Read-only contract getters ───────────────────────────────────────────────

@app.get("/total_participants")
def get_total_participants():
    try:
        return {"TOTAL_PARTICIPANTS": contract.functions.TOTAL_PARTICIPANTS().call()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/participants_list")
def get_participants_list():
    try:
        total        = contract.functions.TOTAL_PARTICIPANTS().call()
        participants = [contract.functions.participantsList(i).call() for i in range(1, total)]
        return {"participantsList": participants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/address_to_slot/{address}")
def get_address_to_slot(address: str):
    try:
        checksum_addr = Web3.to_checksum_address(address)
        slot          = contract.functions.addressToSlot(checksum_addr).call()
        return {"address": checksum_addr, "slot": slot}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/next_available_slot")
def get_next_available_slot():
    try:
        return {"nextAvailableSlot": contract.functions.nextAvailableSlot().call()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/remaining_time_in_phase")
def get_remaining_time_in_phase():
    try:
        return {"remainingTimeInPhase": contract.functions.timeRemaining().call()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current_round")
def get_current_round():
    try:
        return {"currentRound": contract.functions.currentRound().call()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/current_phase")
def get_current_phase():
    try:
        phase     = contract.functions.currentPhase().call()
        phase_map = {0: "DataSubmission", 1: "Execution", 2: "Energy Transfering"}
        return {"currentPhase": phase_map.get(phase, str(phase))}
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
            results.append({"submitter": submitter, "resultHash": result_hash.hex()})
        return {"submittedResults": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result_submission_count")
def get_result_submission_count():
    try:
        return {"resultSubmissionCount": contract.functions.resultSubmissionCount().call()}
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


@app.get("/bidding-results")
def get_bidding_results():
    data = load_bidding_results()
    return {"status": "success", "total_matches": len(data), "data": data}


# ─── Keeper endpoints ─────────────────────────────────────────────────────────

@app.get("/keeper/status")
def keeper_status():
    try:
        time_left     = contract.functions.timeRemaining().call()
        current_phase = contract.functions.currentPhase().call()
        current_round = contract.functions.currentRound().call()

        curr_remaining = get_transfer_window_remaining(current_round)
        prev_remaining = get_transfer_window_remaining(current_round - 1) if current_round > 1 else 0

        return {
            "status":              "running",
            "currentRound":        current_round,
            "currentPhase":        PHASE_NAMES.get(current_phase, str(current_phase)),
            "phaseTimeRemaining":  time_left,
            "willAdvanceIn":       f"{time_left}s" if time_left > 0 else "advancing soon",
            "transferWindows": {
                "currentRound": {
                    "round":              current_round,
                    "isOpen":             curr_remaining > 0,
                    "remainingSeconds":   int(curr_remaining),
                    "remainingFormatted": _fmt(curr_remaining),
                },
                "previousRound": {
                    "round":              current_round - 1,
                    "isOpen":             prev_remaining > 0,
                    "remainingSeconds":   int(prev_remaining),
                    "remainingFormatted": _fmt(prev_remaining),
                } if current_round > 1 else None,
            },
            "canTransfer": curr_remaining > 0 or prev_remaining > 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keeper/force_advance")
def keeper_force_advance():
    try:
        old_phase = contract.functions.currentPhase().call()
        old_round = contract.functions.currentRound().call()
        receipt   = send_transaction(contract.functions.advancePhase())
        new_phase = contract.functions.currentPhase().call()
        new_round = contract.functions.currentRound().call()

        if receipt.status == 1:
            return {
                "status": "success",
                "before": {"round": old_round, "phase": PHASE_NAMES.get(old_phase)},
                "after":  {"round": new_round, "phase": PHASE_NAMES.get(new_phase)},
                "txHash": receipt.transactionHash.hex()
            }
        else:
            raise HTTPException(status_code=400, detail="advancePhase transaction failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Energy transfer ──────────────────────────────────────────────────────────

def load_result_json(path: str = RESULT_FILE) -> List[Dict]:
    with open(path, "r") as f:
        return json.load(f)


def build_address_to_pi_map(pis_json_path: str = PIS_JSON_PATH) -> Dict[str, Dict]:
    with open(pis_json_path, "r") as f:
        pis: Dict = json.load(f)
    mapping = {}
    for name, info in pis.items():
        addr = info.get("eth_address", "").lower()
        if addr:
            mapping[addr] = {
                "name":       name,
                "hostname":   info["hostname"],
                "meter_port": info.get("meter_port", METER_API_PORT),
            }
    return mapping


def meter_url(hostname: str, port: int) -> str:
    return f"http://{hostname}:{port}"


def pi_start_transfer(pi_info, from_hostname, to_hostname, energy_kwh, from_port, to_port):
    url     = f"{meter_url(pi_info['hostname'], pi_info['meter_port'])}/transfer/start"
    payload = {
        "from_pi_ip":   from_hostname,
        "to_pi_ip":     to_hostname,
        "transfer_kwh": energy_kwh,
        "from_port":    from_port,
        "to_port":      to_port
    }
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def pi_poll_transfer_status(pi_info: Dict, label: str) -> Dict:
    url         = f"{meter_url(pi_info['hostname'], pi_info['meter_port'])}/transfer/status"
    retry_count = 0
    MAX_RETRIES = 5

    while True:
        try:
            resp   = requests.get(url, timeout=10)
            resp.raise_for_status()
            status = resp.json()

            if not status.get("active", True):
                return status

            print(f"[transfer/{label}] {pi_info['name']} active... "
                  f"({status.get('current_energy_kwh')} / {status.get('threshold_kwh')} kWh)")
            retry_count = 0

        except requests.exceptions.Timeout:
            retry_count += 1
            print(f"[ERROR][{label}] Timeout contacting {pi_info['name']} (retry {retry_count})")
        except requests.exceptions.ConnectionError:
            retry_count += 1
            print(f"[ERROR][{label}] Connection error with {pi_info['name']} (retry {retry_count})")
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR][{label}] HTTP error from {pi_info['name']}: {e}")
            return {"active": False, "relay_on": None, "stop_reason": "http_error", "error": str(e)}
        except Exception as e:
            print(f"[ERROR][{label}] Unexpected error: {e}")
            return {"active": False, "relay_on": None, "stop_reason": "unexpected_error", "error": str(e)}

        if retry_count >= MAX_RETRIES:
            print(f"[CRITICAL][{label}] Max retries reached for {pi_info['name']}")
            return {"active": False, "relay_on": None, "stop_reason": "connection_lost",
                    "error": f"Lost connection to {pi_info['name']}"}

        time.sleep(TRANSFER_POLL_INTERVAL_S)


def execute_single_match(match: Dict, addr_map: Dict) -> Dict:
    buyer_addr  = match["buyer_id"].lower()
    seller_addr = match["seller_id"].lower()
    energy_kwh  = match["energy_matched"]
    price       = match["price"]

    result = {
        "buyer": match["buyer_id"], "seller": match["seller_id"],
        "energy_kwh": energy_kwh, "price": price,
        "seller_status": None, "buyer_status": None, "error": None,
    }

    seller_info = addr_map.get(seller_addr)
    buyer_info  = addr_map.get(buyer_addr)

    if not seller_info:
        result["error"] = f"Seller {match['seller_id']} not found in pis.json"
        return result
    if not buyer_info:
        result["error"] = f"Buyer {match['buyer_id']} not found in pis.json"
        return result

    print(f"[transfer] {seller_info['name']} -> {buyer_info['name']}  {energy_kwh} kWh @ {price}")

    def start_seller():
        return pi_start_transfer(seller_info,
            from_hostname=seller_info["hostname"], to_hostname=buyer_info["hostname"],
            energy_kwh=energy_kwh, from_port=seller_info["meter_port"], to_port=buyer_info["meter_port"])

    def start_buyer():
        return pi_start_transfer(buyer_info,
            from_hostname=seller_info["hostname"], to_hostname=buyer_info["hostname"],
            energy_kwh=energy_kwh, from_port=seller_info["meter_port"], to_port=buyer_info["meter_port"])

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        sf = pool.submit(start_seller)
        bf = pool.submit(start_buyer)

        try:
            seller_start = sf.result(timeout=20)
            print(f"[transfer] seller started: {seller_start}")
        except Exception as e:
            result["error"] = f"Failed to start transfer on seller {seller_info['name']}: {e}"
            try:
                requests.post(f"{meter_url(buyer_info['hostname'], buyer_info['meter_port'])}/transfer/stop",
                    json={"from_pi_ip": seller_info["hostname"], "to_pi_ip": buyer_info["hostname"], "transfer_kwh": 0},
                    timeout=10)
            except Exception:
                pass
            return result

        try:
            buyer_start = bf.result(timeout=20)
            print(f"[transfer] buyer started: {buyer_start}")
        except Exception as e:
            result["error"] = f"Failed to start transfer on buyer {buyer_info['name']}: {e}"
            try:
                requests.post(f"{meter_url(seller_info['hostname'], seller_info['meter_port'])}/transfer/stop",
                    json={"from_pi_ip": seller_info["hostname"], "to_pi_ip": buyer_info["hostname"], "transfer_kwh": 0},
                    timeout=10)
            except Exception:
                pass
            return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        seller_poll = pool.submit(pi_poll_transfer_status, seller_info, "seller")
        buyer_poll  = pool.submit(pi_poll_transfer_status, buyer_info,  "buyer")

        try:
            result["seller_status"] = seller_poll.result()
        except Exception as e:
            result["seller_status"] = {"error": str(e)}

        try:
            result["buyer_status"] = buyer_poll.result()
        except Exception as e:
            result["buyer_status"] = {"error": str(e)}

    print(f"[transfer] complete — "
          f"seller: {(result.get('seller_status') or {}).get('stop_reason')} | "
          f"buyer: {(result.get('buyer_status') or {}).get('stop_reason')}")

    return result


def execute_seller_group(seller_addr: str, matches: List[Dict], addr_map: Dict) -> List[Dict]:
    """
    Executes all matches for a single seller SEQUENTIALLY.
    Same seller → one transfer at a time.
    """
    results = []
    for i, match in enumerate(matches):
        print(
            f"[transfer] Seller {seller_addr[:10]}... "
            f"match {i+1}/{len(matches)} → buyer {match['buyer_id'][:10]}..."
        )
        result = execute_single_match(match, addr_map)
        results.append(result)

        seller_reason = (result.get("seller_status") or {}).get("stop_reason")
        buyer_reason  = (result.get("buyer_status")  or {}).get("stop_reason")
        error         = result.get("error")

        if error:
            print(f"[transfer] ❌ Match {i+1} failed: {error} — continuing to next match")
        else:
            print(
                f"[transfer] {'✅' if seller_reason == 'THRESHOLD_REACHED' else '⚠️ '} "
                f"Match {i+1} done | seller: {seller_reason} | buyer: {buyer_reason}"
            )

        # small gap between sequential transfers for same seller
        if i < len(matches) - 1:
            print(f"[transfer] ⏳ Waiting 3s before next transfer for same seller...")
            time.sleep(3)

    return results



@app.post("/transfer")
def transfer_energy():
    """
    Reads match_result.json and executes energy transfers.

    Grouping logic:
      - Same seller → sequential  (relay can only handle one at a time)
      - Different sellers → parallel
    
    Example:
      Seller A → Buyer 1  ┐ sequential (same seller)
      Seller A → Buyer 2  ┘
      Seller B → Buyer 3    parallel with Seller A group
    """
    try:
        matches = load_result_json(RESULT_FILE)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{RESULT_FILE} not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in {RESULT_FILE}: {e}")

    if not matches:
        return {"status": "no_matches", "results": []}

    try:
        addr_map = build_address_to_pi_map(PIS_JSON_PATH)
        print("=== ADDRESS MAP ===")
        for addr, info in addr_map.items():
            print(f"  {addr} -> {info['name']} @ {info['hostname']}:{info['meter_port']}")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pis.json not found")

    # ── Group matches by seller ───────────────────────────────────────────────
    seller_groups: Dict[str, List[Dict]] = {}
    for match in matches:
        seller = match["seller_id"].lower()
        if seller not in seller_groups:
            seller_groups[seller] = []
        seller_groups[seller].append(match)

    print(f"\n=== TRANSFER GROUPS ===")
    for seller, group in seller_groups.items():
        print(f"  Seller {seller[:10]}... → {len(group)} match(es):")
        for m in group:
            print(f"      → Buyer {m['buyer_id'][:10]}... | {m['energy_matched']} kWh @ {m['price']}")

    # ── Run each seller group in parallel, matches within group sequential ───
    all_results: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(seller_groups)) as pool:
        futures = {
            pool.submit(execute_seller_group, seller, group, addr_map): seller
            for seller, group in seller_groups.items()
        }
        for future in concurrent.futures.as_completed(futures):
            seller = futures[future]
            try:
                group_results = future.result()
                all_results.extend(group_results)
            except Exception as e:
                # whole seller group failed
                for match in seller_groups[seller]:
                    all_results.append({
                        "buyer":         match.get("buyer_id"),
                        "seller":        match.get("seller_id"),
                        "energy_kwh":    match.get("energy_matched"),
                        "price":         match.get("price"),
                        "seller_status": None,
                        "buyer_status":  None,
                        "error":         str(e),
                    })

    success_count = sum(
        1 for r in all_results
        if r.get("error") is None
        and (r.get("seller_status") or {}).get("stop_reason") == "THRESHOLD_REACHED"
        and (r.get("buyer_status")  or {}).get("stop_reason") == "THRESHOLD_REACHED"
    )

    return {
        "status":        "completed",
        "total_matches": len(matches),
        "succeeded":     success_count,
        "failed":        len(matches) - success_count,
        "results":       all_results,
    }




# @app.post("/transfer")
# def transfer_energy():
#     try:
#         matches = load_result_json(RESULT_FILE)
#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail=f"{RESULT_FILE} not found")
#     except json.JSONDecodeError as e:
#         raise HTTPException(status_code=400, detail=f"Invalid JSON in {RESULT_FILE}: {e}")

#     if not matches:
#         return {"status": "no_matches", "results": []}

#     try:
#         addr_map = build_address_to_pi_map(PIS_JSON_PATH)
#         print("=== ADDRESS MAP ===")
#         for addr, info in addr_map.items():
#             print(f"  {addr} -> {info['name']} @ {info['hostname']}:{info['meter_port']}")
#         matches = load_result_json(RESULT_FILE)
#         print("=== MATCHES ===")
#         for m in matches:
#             print(f"  buyer:  {m['buyer_id'].lower()}\n  seller: {m['seller_id'].lower()}")
#     except FileNotFoundError:
#         raise HTTPException(status_code=500, detail="pis.json not found")

#     results: List[Dict[str, Any]] = []

#     with concurrent.futures.ThreadPoolExecutor(max_workers=len(matches)) as pool:
#         futures = {pool.submit(execute_single_match, match, addr_map): match for match in matches}
#         for future in concurrent.futures.as_completed(futures):
#             try:
#                 results.append(future.result())
#             except Exception as e:
#                 original = futures[future]
#                 results.append({"buyer": original.get("buyer_id"), "seller": original.get("seller_id"), "error": str(e)})

#     success_count = sum(
#         1 for r in results
#         if r.get("error") is None
#         and (r.get("seller_status") or {}).get("stop_reason") == "THRESHOLD_REACHED"
#         and (r.get("buyer_status")  or {}).get("stop_reason") == "THRESHOLD_REACHED"
#     )

#     return {
#         "status":        "completed",
#         "total_matches": len(matches),
#         "succeeded":     success_count,
#         "failed":        len(matches) - success_count,
#         "results":       results,
#     }


@app.get("/transfer/status/{hostname}")
def get_transfer_status_for_pi(hostname: str):
    try:
        with open(PIS_JSON_PATH) as f:
            pis = json.load(f)
        port = METER_API_PORT
        for info in pis.values():
            if info.get("hostname") == hostname:
                port = info.get("meter_port", METER_API_PORT)
                break
        resp = requests.get(f"http://{hostname}:{port}/transfer/status", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    local_ip = get_local_ip()
    print("\n🚀 P2P Energy Trading API running!")
    print(f"   → Local Access:   http://localhost:8000")
    print(f"   → Network Access: http://{local_ip}:8000\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)