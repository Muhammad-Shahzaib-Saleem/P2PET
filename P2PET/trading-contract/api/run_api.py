# import paramiko
# import time

# # Remote Pi details
# host = "100.120.124.29"   # Remote Pi IP
# username = "pi"
# password = "Lums12345"
# port = 8001


# host1 = "100.93.80.36"
# username1 = "pi"
# password1 = "Lums12345"
# port1 = 8002
# # Command to start FastAPI
# command = f"cd /home/pi/Desktop/P2PET_Dynamic/P2PET && source venv/bin/activate && cd p2p-energy-trading-contract/api && nohup python meter_api.py > meter.log 2>&1 &"

# # SSH connection
# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect(hostname=host, username=username, password=password)

# # Run API
# client.exec_command(command)

# # Wait a bit for server to start
# time.sleep(3)



# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect(hostname=host1, username=username1, password=password1)

# # Run API
# client.exec_command(command)

# # Wait a bit for server to start
# time.sleep(3)



# # Construct API URL
# api_url = f"http://{host}:{port}"
# api_url1 = f"http://{host1}:{port1}"
# print("✅ API of pi_15 is running at:")
# print(api_url)

# print("✅ API of pi_2 is running at:")
# print(api_url1)

# client.close()

"""
start_all_pis.py
────────────────
SSHes into every Pi in PI_NODES, starts meter_api.py on its assigned port,
and prints the resulting API URLs.

Run once on the master Pi:
    python start_all_pis.py
"""

import paramiko
import time

# ─── Pi node registry ─────────────────────────────────────────────────────────
# Add as many Pis as you have. Each gets its own port.

PI_NODES = [
    # {"name": "pi_1",  "host": "100.76.91.82",      "username": "pi", "password": "Lums12345", "port": 8001},
    {"name": "pi_2",  "host": "100.93.80.36",   "username": "pi", "password": "Lums12345", "port": 8002},
    {"name": "pi_15", "host": "100.120.124.29", "username": "pi", "password": "Lums12345", "port": 8003},
    
    
    # {"name": "pi_4",  "host": "100.x.x.x",      "username": "pi", "password": "Lums12345", "port": 8004},
]

PROJECT_DIR = "/home/pi/Desktop/P2PET_Dynamic/P2PET"
VENV_ACTIVATE = f"source {PROJECT_DIR}/venv/bin/activate"
API_DIR = f"{PROJECT_DIR}/p2p-energy-trading-contract/api"

# ─── Start one Pi ─────────────────────────────────────────────────────────────

def start_pi(node: dict) -> bool:
    """SSH into one Pi, kill any old instance, start fresh on the given port."""
    name     = node["name"]
    host     = node["host"]
    username = node["username"]
    password = node["password"]
    port     = node["port"]

    print(f"\n[{name}] Connecting to {host} ...")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname=host, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"[{name}] ❌ SSH connection failed: {e}")
        return False

    # Kill any existing instance on this port
    kill_cmd = f"fuser -k {port}/tcp 2>/dev/null || pkill -f 'meter_api.py' 2>/dev/null || true"
    _, stdout, _ = client.exec_command(kill_cmd)
    stdout.channel.recv_exit_status()   # wait for it to finish
    time.sleep(0.5)

    # Pre-flight: check the directory and python exist
    _, out, _ = client.exec_command(f"ls {API_DIR}/meter_api.py 2>&1")
    check = out.read().decode().strip()
    if "No such file" in check or not check:
        print(f"[{name}] ❌ meter_api.py not found at {API_DIR}")
        print(f"[{name}]    Got: {check}")
        client.close()
        return False

    _, out, _ = client.exec_command(f"{VENV_ACTIVATE} && python --version 2>&1")
    py_version = out.read().decode().strip()
    print(f"[{name}] Python: {py_version}")

    # Start meter_api.py with the correct port
    start_cmd = (
        f"cd {API_DIR} && "
        f"{VENV_ACTIVATE} && "
        f"nohup python meter_api.py --port {port} > meter_{port}.log 2>&1 &"
    )
    _, stdout, stderr = client.exec_command(start_cmd)
    stdout.channel.recv_exit_status()

    # Give it a moment to boot
    time.sleep(3)

    # Verify it's actually running
    _, stdout, _ = client.exec_command("pgrep -fa meter_api.py")
    procs = stdout.read().decode().strip()

    # Fetch log regardless so we can show errors
    _, log_out, _ = client.exec_command(
        f"tail -n 30 {API_DIR}/meter_{{port}}.log 2>/dev/null || echo '(log not found)'"
    )
    log_content = log_out.read().decode().strip()

    client.close()

    if procs:
        print(f"[{name}] ✅ Running  →  http://{host}:{port}")
        return True
    else:
        print(f"[{name}] ❌ Process did not start. Log output:")
        print(f"[{name}] ─────────────────────────────────────────")
        for line in log_content.splitlines():
            print(f"[{name}]   {line}")
        print(f"[{name}] ─────────────────────────────────────────")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  Starting meter_api.py on all Pi nodes")
    print("=" * 55)

    success = []
    failed  = []

    for node in PI_NODES:
        if start_pi(node):
            success.append(node)
        else:
            failed.append(node)

    print("\n" + "=" * 55)
    print(f"  Done — {len(success)} started, {len(failed)} failed")
    print("=" * 55)

    if success:
        print("\n✅ Online APIs:")
        for node in success:
            print(f"   {node['name']:10s}  http://{node['host']}:{node['port']}")

    if failed:
        print("\n❌ Failed:")
        for node in failed:
            print(f"   {node['name']:10s}  {node['host']}")