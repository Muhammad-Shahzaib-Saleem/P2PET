# """
# run_display.py
# ──────────────
# Run this on YOUR machine:
#     python run_display.py

# It will:
# 1. Copy display.py to the Pi (if changed)
# 2. SSH into the Pi and run it with sudo
# 3. Stream all output back to your terminal
# 4. Ctrl+C cleanly stops it on the Pi too

# Requirements (on YOUR machine):
#     pip install paramiko scp
# """

# import paramiko
# import sys
# import os

# # ═══════════════════════════════════════════════════════════════════
# #  CONFIG
# # ═══════════════════════════════════════════════════════════════════

# PI_HOST     = "100.93.80.36"   # change to your Pi's IP
# PI_USER     = "pi"
# PI_PASS     = "Lums12345"
# PI_SCRIPT   = "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/api/display.py"   # where to put display.py on the Pi
# LOCAL_SCRIPT = "display.py"      # must be in same folder as this file

# # ═══════════════════════════════════════════════════════════════════
# #  MAIN
# # ═══════════════════════════════════════════════════════════════════

# def main():
#     client = paramiko.SSHClient()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#     print(f"[*] Connecting to {PI_USER}@{PI_HOST} ...")
#     try:
#         client.connect(PI_HOST, username=PI_USER, password=PI_PASS, timeout=10)
#     except Exception as e:
#         print(f"[!] SSH connection failed: {e}")
#         sys.exit(1)

#     # ── Upload latest display.py to Pi ──────────────────────────────
#     if os.path.exists(LOCAL_SCRIPT):
#         print(f"[*] Uploading {LOCAL_SCRIPT} → {PI_SCRIPT}")
#         sftp = client.open_sftp()
#         sftp.put(LOCAL_SCRIPT, PI_SCRIPT)
#         sftp.close()
#         print(f"[*] Upload done.")
#     else:
#         print(f"[!] {LOCAL_SCRIPT} not found locally — using existing file on Pi.")

#     # ── Fix FB permission ────────────────────────────────────────────
#     print(f"[*] Fixing /dev/fb1 permissions ...")
#     client.exec_command("sudo chmod 666 /dev/fb1")

#     # ── Run display.py on Pi ─────────────────────────────────────────
#     cmd = f"sudo python {PI_SCRIPT}"
#     print(f"[*] Running: {cmd}")
#     print(f"[*] Streaming output — press Ctrl+C to stop\n")
#     print("─" * 50)

#     transport = client.get_transport()
#     channel   = transport.open_session()
#     channel.get_pty()
#     channel.exec_command(cmd)

#     try:
#         while True:
#             if channel.recv_ready():
#                 out = channel.recv(1024).decode(errors="replace")
#                 print(out, end="", flush=True)
#             if channel.recv_stderr_ready():
#                 err = channel.recv_stderr(1024).decode(errors="replace")
#                 print(err, end="", flush=True)
#             if channel.exit_status_ready():
#                 break
#     except KeyboardInterrupt:
#         print("\n[*] Ctrl+C — stopping display on Pi ...")
#         channel.send("\x03")   # send Ctrl+C to the remote process
#         import time; time.sleep(1)

#     channel.close()
#     client.close()
#     print("[*] Done.")


# if __name__ == "__main__":
#     main()





import paramiko
import sys
import threading
import time

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

PI_NODES = [
    {"host": "100.93.80.36",   "api_port": 8002},
    {"host": "100.71.238.87", "api_port": 8003},
    {"host": "100.80.205.106", "api_port": 8004},
    {"host": "100.120.139.128", "api_port": 8005},
    {"host": "100.80.11.48", "api_port": 8006},
    {"host": "100.120.124.29", "api_port": 8007},

    # 👉 add more Pis here
]

PI_USER = "pi"
PI_PASS = "Lums12345"

PI_SCRIPT = "/home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/api/display.py"

# ═══════════════════════════════════════════════════════════════════
# WORKER
# ═══════════════════════════════════════════════════════════════════

def run_on_pi(node):
    host = node["host"]
    port = node["api_port"]

    prefix = f"[{host}] "

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(prefix + "Connecting...")
        client.connect(host, username=PI_USER, password=PI_PASS, timeout=10)

        # permissions (optional but safe for framebuffer)
        client.exec_command("sudo chmod 666 /dev/fb1")

        # per-pi API base (IMPORTANT FIX)
        api_base = f"http://127.0.0.1:{port}"

        cmd = f"API_BASE={api_base}  python3 {PI_SCRIPT}"

        print(prefix + f"Running display.py with API_BASE={api_base}")

        transport = client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel.exec_command(cmd)

        while True:
            if channel.recv_ready():
                print(prefix + channel.recv(1024).decode(errors="replace"), end="")

            if channel.recv_stderr_ready():
                print(prefix + channel.recv_stderr(1024).decode(errors="replace"), end="")

            if channel.exit_status_ready():
                break

            time.sleep(0.1)

    except Exception as e:
        print(prefix + f"ERROR: {e}")

    finally:
        client.close()
        print(prefix + "Disconnected")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    threads = []

    print("[*] Starting multi-Pi display controller...\n")

    for node in PI_NODES:
        t = threading.Thread(target=run_on_pi, args=(node,))
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[*] Stopping all Pis...")
        sys.exit(0)


if __name__ == "__main__":
    main()