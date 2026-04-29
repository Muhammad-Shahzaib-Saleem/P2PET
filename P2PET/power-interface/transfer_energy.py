# """
# energy_transfer(from_pi_ip, to_pi_ip, transfer_energy_kwh)

# Energy tracking logic:
#   - FROM pi  →  forward energy register 0x004B (/800)  — energy being SENT
#   - TO   pi  →  reverse energy register 0x004E (/800)  — energy being RECEIVED
#   - Relay cuts off when TO pi reverse delta >= transfer_energy_kwh

# Install on your controller machine:
#     pip install paramiko
# """

# import time
# import paramiko

# # ──────────────────────────────────────────────────────────────────────────────
# # Reader scripts — uploaded via SFTP and run remotely
# # ──────────────────────────────────────────────────────────────────────────────

# # FROM pi: forward energy (0x004B, /800) — energy being exported/sent
# READER_FORWARD_SCRIPT = """\
# import serial
# import RPi.GPIO as GPIO

# CMD = bytes([0x01, 0x03, 0x00, 0x4B, 0x00, 0x02, 0xB4, 0x1D])

# DE_PIN = 18
# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(DE_PIN, GPIO.OUT)
# GPIO.output(DE_PIN, GPIO.LOW)

# ser = serial.Serial("/dev/serial0", 9600, bytesize=8,
#                     parity="N", stopbits=1, timeout=0.5)

# GPIO.output(DE_PIN, GPIO.HIGH)
# ser.write(CMD)
# ser.flush()
# GPIO.output(DE_PIN, GPIO.LOW)

# resp = ser.read(9)
# ser.close()
# GPIO.cleanup()

# if len(resp) == 9:
#     raw = (resp[3] << 24) | (resp[4] << 16) | (resp[5] << 8) | resp[6]
#     print(raw / 800.0)
# else:
#     print("ERROR: got " + str(len(resp)) + " bytes: " + resp.hex())
# """

# # TO pi: reverse energy (0x004E, /800) — energy being imported/received
# READER_REVERSE_SCRIPT = """\
# import serial
# import RPi.GPIO as GPIO

# CMD = bytes([0x01, 0x03, 0x00, 0x4E, 0x00, 0x02, 0xA4, 0x1C])

# DE_PIN = 18
# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(DE_PIN, GPIO.OUT)
# GPIO.output(DE_PIN, GPIO.LOW)

# ser = serial.Serial("/dev/serial0", 9600, bytesize=8,
#                     parity="N", stopbits=1, timeout=0.5)

# GPIO.output(DE_PIN, GPIO.HIGH)
# ser.write(CMD)
# ser.flush()
# GPIO.output(DE_PIN, GPIO.LOW)

# resp = ser.read(9)
# ser.close()
# GPIO.cleanup()

# if len(resp) == 9:
#     raw = (resp[3] << 24) | (resp[4] << 16) | (resp[5] << 8) | resp[6]
#     print(raw / 800.0)
# else:
#     print("ERROR: got " + str(len(resp)) + " bytes: " + resp.hex())
# """

# # ──────────────────────────────────────────────────────────────────────────────
# # Relay scripts — use lgpio directly (avoids RPi.GPIO 'not allocated' bug)
# # Active-LOW relay:  0 = ON (energised),  1 = OFF (released)
# # ──────────────────────────────────────────────────────────────────────────────

# RELAY_ON_SCRIPT = """\
# import lgpio
# h = lgpio.gpiochip_open(0)
# lgpio.gpio_claim_output(h, {pin})
# lgpio.gpio_write(h, {pin}, 0)
# """

# RELAY_OFF_SCRIPT = """\
# import lgpio
# h = lgpio.gpiochip_open(0)
# lgpio.gpio_claim_output(h, {pin})
# lgpio.gpio_write(h, {pin}, 1)
# lgpio.gpiochip_close(h)
# """

# REMOTE_READER_FWD = "/tmp/read_energy_fwd.py"
# REMOTE_READER_REV = "/tmp/read_energy_rev.py"
# REMOTE_RELAY_ON   = "/tmp/relay_on.py"
# REMOTE_RELAY_OFF  = "/tmp/relay_off.py"

# # ──────────────────────────────────────────────────────────────────────────────
# # SSH / SFTP helpers
# # ──────────────────────────────────────────────────────────────────────────────

# def _ssh_connect(ip: str, username: str, password: str,
#                  port: int = 22) -> paramiko.SSHClient:
#     client = paramiko.SSHClient()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     client.connect(hostname=ip, port=port, username=username,
#                    password=password, timeout=10)
#     return client


# def _run(client: paramiko.SSHClient, cmd: str) -> tuple[str, str]:
#     _, stdout, stderr = client.exec_command(cmd)
#     return stdout.read().decode().strip(), stderr.read().decode().strip()


# def _upload(client: paramiko.SSHClient, content: str, remote_path: str):
#     sftp = client.open_sftp()
#     with sftp.file(remote_path, "w") as f:
#         f.write(content)
#     sftp.close()


# # ──────────────────────────────────────────────────────────────────────────────
# # Energy reading
# # ──────────────────────────────────────────────────────────────────────────────

# def _read_forward_kwh(client: paramiko.SSHClient) -> float:
#     """Read forward (sent) energy from FROM pi."""
#     _upload(client, READER_FORWARD_SCRIPT, REMOTE_READER_FWD)
#     stdout, stderr = _run(client, f"python3 {REMOTE_READER_FWD}")
#     if not stdout or stdout.startswith("ERROR"):
#         raise ValueError(f"Forward read failed. stdout={stdout!r} stderr={stderr!r}")
#     return float(stdout)


# def _read_reverse_kwh(client: paramiko.SSHClient) -> float:
#     """Read reverse (received) energy from TO pi."""
#     _upload(client, READER_REVERSE_SCRIPT, REMOTE_READER_REV)
#     stdout, stderr = _run(client, f"python3 {REMOTE_READER_REV}")
#     if not stdout or stdout.startswith("ERROR"):
#         raise ValueError(f"Reverse read failed. stdout={stdout!r} stderr={stderr!r}")
#     return float(stdout)


# # ──────────────────────────────────────────────────────────────────────────────
# # Relay control
# # ──────────────────────────────────────────────────────────────────────────────

# def _relay_on(client: paramiko.SSHClient, pin: int):
#     _upload(client, RELAY_ON_SCRIPT.format(pin=pin), REMOTE_RELAY_ON)
#     stdout, stderr = _run(client, f"python3 {REMOTE_RELAY_ON}")
#     if stderr:
#         print(f"[relay_on]  stderr: {stderr}")
#     else:
#         print(f"[relay_on]  OK — pin {pin} LOW (relay energised)")


# def _relay_off(client: paramiko.SSHClient, pin: int):
#     _upload(client, RELAY_OFF_SCRIPT.format(pin=pin), REMOTE_RELAY_OFF)
#     stdout, stderr = _run(client, f"python3 {REMOTE_RELAY_OFF}")
#     if stderr:
#         print(f"[relay_off] stderr: {stderr}")
#     else:
#         print(f"[relay_off] OK — pin {pin} HIGH (relay released)")


# # ──────────────────────────────────────────────────────────────────────────────
# # Main transfer function
# # ──────────────────────────────────────────────────────────────────────────────

# def transfer_energy(
#     from_pi_ip: str,
#     to_pi_ip: str,
#     transfer_energy_kwh: float,
#     *,
#     username: str = "pi",
#     password: str,
#     port: int = 22,
#     relay_pin: int = 27,
#     poll_interval: float = 2.0,
#     max_duration: float = 3600.0,
# ) -> dict:
#     """
#     Transfer energy from FROM pi to TO pi.

#     Tracking:
#       FROM pi — forward energy delta  (what it's sending out)
#       TO   pi — reverse energy delta  (what it's receiving)
#       Relay OFF when TO pi reverse delta >= transfer_energy_kwh

#     Parameters
#     ----------
#     from_pi_ip          : IP of Pi with the energy meter (sender)
#     to_pi_ip            : IP of Pi with the relay + meter (receiver)
#     transfer_energy_kwh : kWh target — relay cuts off once TO pi received this
#     username            : SSH username (default "pi")
#     password            : SSH password
#     port                : SSH port (default 22)
#     relay_pin           : BCM GPIO pin for relay on TO pi (default 17)
#     poll_interval       : Seconds between meter reads (default 2)
#     max_duration        : Safety timeout in seconds (default 3600)

#     Returns
#     -------
#     dict: success, from_baseline_kwh, to_baseline_kwh,
#           from_sent_kwh, to_received_kwh,
#           elapsed_seconds, message
#     """

#     result = {
#         "success": False,
#         "from_baseline_kwh": None,
#         "to_baseline_kwh": None,
#         "from_sent_kwh": 0.0,
#         "to_received_kwh": 0.0,
#         "elapsed_seconds": 0.0,
#         "message": "",
#     }

#     from_ssh = to_ssh = None

#     try:
#         # ── 1. Connect ────────────────────────────────────────────────────────
#         print(f"[transfer_energy] Connecting to FROM pi ({from_pi_ip}) ...")
#         from_ssh = _ssh_connect(from_pi_ip, username, password, port)

#         print(f"[transfer_energy] Connecting to TO   pi ({to_pi_ip}) ...")
#         to_ssh = _ssh_connect(to_pi_ip, username, password, port)

#         # ── 2. Baselines — read both meters before relay turns on ─────────────
#         print("[transfer_energy] Reading baselines ...")
#         from_baseline = _read_forward_kwh(from_ssh)
#         to_baseline   = _read_reverse_kwh(to_ssh)

#         result["from_baseline_kwh"] = from_baseline
#         result["to_baseline_kwh"]   = to_baseline

#         print(f"[transfer_energy] FROM baseline (fwd): {from_baseline:.4f} kWh")
#         print(f"[transfer_energy] TO   baseline (rev): {to_baseline:.4f} kWh")

#         # ── 3. Turn relay ON ──────────────────────────────────────────────────
#         print(f"[transfer_energy] Relay ON  (pin {relay_pin}) on TO pi ...")
#         _relay_on(to_ssh, relay_pin)

#         # ── 4. Poll both meters — stop on TO pi received delta ────────────────
#         start_time   = time.time()
#         from_current = from_baseline
#         to_current   = to_baseline
#         from_sent    = 0.0
#         to_received  = 0.0

#         print(f"[transfer_energy] Polling every {poll_interval}s "
#               f"— target {transfer_energy_kwh:.4f} kWh received by TO pi ...")

#         while True:
#             elapsed = time.time() - start_time

#             if elapsed >= max_duration:
#                 result["message"] = (
#                     f"Timeout after {max_duration}s. "
#                     f"TO received {to_received:.4f} kWh, "
#                     f"FROM sent {from_sent:.4f} kWh."
#                 )
#                 print(f"[transfer_energy] TIMEOUT — {result['message']}")
#                 break

#             time.sleep(poll_interval)

#             # Read FROM pi forward energy
#             try:
#                 from_current = _read_forward_kwh(from_ssh)
#                 from_sent    = from_current - from_baseline
#             except ValueError as e:
#                 print(f"[transfer_energy] FROM read error (retrying): {e}")

#             # Read TO pi reverse energy  ← this is what controls the cutoff
#             try:
#                 to_current  = _read_reverse_kwh(to_ssh)
#                 to_received = to_current - to_baseline
#             except ValueError as e:
#                 print(f"[transfer_energy] TO read error (retrying): {e}")
#                 continue

#             print(
#                 f"[transfer_energy] "
#                 f"FROM sent: {from_sent:.4f} kWh  |  "
#                 f"TO received: {to_received:.4f} / {transfer_energy_kwh:.4f} kWh  |  "
#                 f"{elapsed:.0f}s"
#             )

#             if to_received >= transfer_energy_kwh:
#                 result["message"] = (
#                     f"Target reached: TO received {to_received:.4f} kWh "
#                     f"(FROM sent {from_sent:.4f} kWh) in {elapsed:.1f}s."
#                 )
#                 result["success"] = True
#                 print(f"[transfer_energy] ✓ {result['message']}")
#                 break

#         result["from_sent_kwh"]   = from_sent
#         result["to_received_kwh"] = to_received
#         result["elapsed_seconds"] = time.time() - start_time

#     except Exception as exc:
#         result["message"] = f"Fatal error: {exc}"
#         print(f"[transfer_energy] ERROR: {exc}")

#     finally:
#         # ── 5. Always turn relay OFF ──────────────────────────────────────────
#         if to_ssh:
#             print(f"[transfer_energy] Relay OFF (pin {relay_pin}) on TO pi ...")
#             try:
#                 _relay_off(to_ssh, relay_pin)
#             except Exception as e:
#                 print(f"[transfer_energy] Could not turn relay off: {e}")
#             to_ssh.close()

#         if from_ssh:
#             from_ssh.close()

#     return result


# # ──────────────────────────────────────────────────────────────────────────────
# # Example usage
# # ──────────────────────────────────────────────────────────────────────────────

# if __name__ == "__main__":
#     summary = transfer_energy(
#         from_pi_ip          = "100.120.124.29",
#         to_pi_ip            = "100.93.80.36",
#         transfer_energy_kwh = 0.2,
#         username            = "pi",
#         password            = "Lums12345",
#         relay_pin           = 27,
#         poll_interval       = 2.0,
#         max_duration        = 3600.0,
#     )

#     print("\n── Transfer Summary ──────────────────────────────")
#     for k, v in summary.items():
#         print(f"  {k:20s}: {v}")


import time
import paramiko

# ─────────────────────────────────────────────
# ROBUST METER READER (FIXED RS485 TIMING)
# ─────────────────────────────────────────────

READER_FORWARD_SCRIPT = """\
import serial
import RPi.GPIO as GPIO
import time

CMD = bytes([0x01, 0x03, 0x00, 0x4B, 0x00, 0x02, 0xB4, 0x1D])
DE_PIN = 18

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(DE_PIN, GPIO.OUT)

ser = serial.Serial("/dev/serial0", 9600, timeout=1)
ser.reset_input_buffer()

GPIO.output(DE_PIN, 1)
time.sleep(0.05)
ser.write(CMD)
ser.flush()

time.sleep(0.1)  # IMPORTANT: wait for RS485 response

GPIO.output(DE_PIN, 0)

resp = ser.read(9)

ser.close()
GPIO.cleanup()

if len(resp) == 9:
    raw = (resp[3] << 24) | (resp[4] << 16) | (resp[5] << 8) | resp[6]
    print(raw / 800.0)
else:
    print("ERROR: got", len(resp), "bytes:", resp.hex())
"""

READER_REVERSE_SCRIPT = """\
import serial
import RPi.GPIO as GPIO
import time

CMD = bytes([0x01, 0x03, 0x00, 0x4E, 0x00, 0x02, 0xA4, 0x1C])
DE_PIN = 18

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(DE_PIN, GPIO.OUT)

ser = serial.Serial("/dev/serial0", 9600, timeout=1)
ser.reset_input_buffer()

GPIO.output(DE_PIN, 1)
time.sleep(0.05)
ser.write(CMD)
ser.flush()

time.sleep(0.1)

GPIO.output(DE_PIN, 0)

resp = ser.read(9)

ser.close()
GPIO.cleanup()

if len(resp) == 9:
    raw = (resp[3] << 24) | (resp[4] << 16) | (resp[5] << 8) | resp[6]
    print(raw / 800.0)
else:
    print("ERROR: got", len(resp), "bytes:", resp.hex())
"""

# ─────────────────────────────────────────────
# RELAY (STABLE VERSION USING lgpio)
# ─────────────────────────────────────────────

RELAY_ON_SCRIPT = """\
import lgpio
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, {pin})
lgpio.gpio_write(h, {pin}, 0)
lgpio.gpiochip_close(h)
"""

RELAY_OFF_SCRIPT = """\
import lgpio
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, {pin})
lgpio.gpio_write(h, {pin}, 1)
lgpio.gpiochip_close(h)
"""

# ─────────────────────────────────────────────
# SSH HELPERS
# ─────────────────────────────────────────────

def ssh_connect(ip, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=password)
    return client


def run(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode().strip(), stderr.read().decode().strip()


def upload(client, content, path):
    sftp = client.open_sftp()
    with sftp.file(path, "w") as f:
        f.write(content)
    sftp.close()

# ─────────────────────────────────────────────
# SAFE READ FUNCTION (RETRY FIX)
# ─────────────────────────────────────────────

def safe_read(client, script, path, retries=3):
    upload(client, script, path)

    for i in range(retries):
        out, err = run(client, f"python3 {path}")
        if out and not out.startswith("ERROR"):
            return float(out)
        time.sleep(0.5)

    raise ValueError(f"Meter read failed after retries: {out} {err}")

# ─────────────────────────────────────────────
# RELAY CONTROL
# ─────────────────────────────────────────────

def relay_on(client, pin, path):
    upload(client, RELAY_ON_SCRIPT.format(pin=pin), path)
    run(client, f"python3 {path}")


def relay_off(client, pin, path):
    upload(client, RELAY_OFF_SCRIPT.format(pin=pin), path)
    run(client, f"python3 {path}")

# ─────────────────────────────────────────────
# MAIN FUNCTION (UNCHANGED LOGIC, FIXED STABILITY)
# ─────────────────────────────────────────────

def transfer_energy(from_pi_ip, to_pi_ip, kwh, user="pi", password="pass", relay_pin=27):

    from_client = ssh_connect(from_pi_ip, user, password)
    to_client = ssh_connect(to_pi_ip, user, password)

    print("[+] Reading baseline...")
    f_base = safe_read(from_client, READER_FORWARD_SCRIPT, "/tmp/fwd.py")
    t_base = safe_read(to_client, READER_REVERSE_SCRIPT, "/tmp/rev.py")

    print("[+] Relay ON")
    relay_on(to_client, relay_pin, "/tmp/relay_on.py")

    sent = 0
    received = 0
    start = time.time()

    while True:
        time.sleep(2)

        try:
            sent = safe_read(from_client, READER_FORWARD_SCRIPT, "/tmp/fwd.py") - f_base
            received = safe_read(to_client, READER_REVERSE_SCRIPT, "/tmp/rev.py") - t_base
        except Exception as e:
            print("[WARN]", e)
            continue

        print(f"Sent={sent:.4f} kWh | Received={received:.4f} kWh")

        if received >= kwh:
            print("[✓] Target reached")
            break

    print("[+] Relay OFF")
    relay_off(to_client, relay_pin, "/tmp/relay_off.py")

    from_client.close()
    to_client.close()

    return {
        "sent": sent,
        "received": received,
        "time": time.time() - start
    }


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print(transfer_energy(
        "100.120.124.29",
        "100.93.80.36",
        0.2,
        password="Lums12345"
    ))