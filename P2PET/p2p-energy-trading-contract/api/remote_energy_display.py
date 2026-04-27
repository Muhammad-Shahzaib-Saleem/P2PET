# #!/usr/bin/env python3
# """
# Energy Display - Remote Runner
# Run this from YOUR machine:
#     python energy_display.py

# It will SSH into the Pi, upload itself, install dependencies, and run.
# Edit the PI_HOST, PI_USER, PI_PASSWORD below before running.
# """

# import subprocess
# import sys
# import os
# import tempfile

# # ─────────────────────────────────────────────
# #  CONFIGURE THESE
# # ─────────────────────────────────────────────
# PI_HOST     = "100.120.124.29"   # ← Your Pi's IP address
# PI_USER     = "pi"              # ← Your Pi's username
# PI_PASSWORD = "Lums12345"       # ← Your Pi's password
# # ─────────────────────────────────────────────

# # The actual display code that runs ON the Pi
# DISPLAY_CODE = r'''
# import serial
# import RPi.GPIO as GPIO
# import time
# import os
# import numpy as np
# from PIL import Image, ImageDraw, ImageFont

# # ================= GPIO =================
# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)

# DE_PIN = 18
# GPIO.setup(DE_PIN, GPIO.OUT)
# GPIO.output(DE_PIN, GPIO.LOW)

# relay_state = True

# # ================= FRAMEBUFFER =================
# FB_DEV  = "/dev/fb1"
# WIDTH   = 480
# HEIGHT  = 320

# # ================= COLORS =================
# BG_COLOR      = (10, 18, 28)
# CARD_COLOR    = (20, 32, 48)
# ACCENT_COLOR  = (0, 255, 140)
# TEXT_COLOR    = (230, 255, 245)
# SUBTEXT_COLOR = (120, 180, 160)
# WARN_COLOR    = (255, 140, 60)

# # ================= PAGE =================
# current_page = 0

# # ================= LIVE SMOOTH STORAGE =================
# last_valid = {
#     "voltage": None,
#     "current": None,
#     "power": None,
#     "pf": None,
#     "forward_energy": None,
#     "reverse_energy": None,
# }

# smooth_values = {
#     "voltage": None,
#     "current": None,
#     "power": None,
#     "pf": None,
#     "forward_energy": None,
#     "reverse_energy": None,
# }

# # ================= FONTS =================
# def get_font(size):
#     try:
#         return ImageFont.truetype(
#             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size
#         )
#     except:
#         return ImageFont.load_default()

# font_micro = get_font(11)
# font_small = get_font(15)

# def load_fonts():
#     global font_micro, font_small
#     font_micro = get_font(11)
#     font_small = get_font(15)

# # ================= MODBUS =================
# def modbus_crc16(data: bytes) -> int:
#     crc = 0xFFFF
#     for b in data:
#         crc ^= b
#         for _ in range(8):
#             crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
#     return crc & 0xFFFF

# CMD_VOLTAGE_A      = bytes.fromhex("01 03 00 48 00 01 04 1C")
# CMD_CURRENT_A      = bytes.fromhex("01 03 00 49 00 01 55 DC")
# CMD_POWER_A        = bytes.fromhex("01 03 00 4A 00 01 A5 DC")
# CMD_PF_A           = bytes.fromhex("01 03 00 4D 00 01 14 1D")
# CMD_ENERGY_FWD_OLD = bytes.fromhex("01 03 00 4B 00 02 B4 1D")
# CMD_ENERGY_REV_OLD = bytes.fromhex("01 03 00 4E 00 02 A4 1C")

# ser = serial.Serial("/dev/serial0", baudrate=9600, timeout=0.8)

# def tx(): GPIO.output(DE_PIN, GPIO.HIGH)
# def rx(): GPIO.output(DE_PIN, GPIO.LOW)

# def send_and_read(cmd, n):
#     ser.reset_input_buffer()
#     tx(); ser.write(cmd); ser.flush()
#     time.sleep(0.004)
#     rx(); time.sleep(0.002)

#     resp = ser.read(n)
#     if len(resp) != n:
#         return None
#     if resp[0] != 1 or resp[1] != 3:
#         return None
#     if (resp[-2] | (resp[-1] << 8)) != modbus_crc16(resp[:-2]):
#         return None
#     return resp

# def decode_u16(r): return (r[3] << 8) | r[4]
# def decode_u32(r): return (r[3] << 24) | (r[4] << 16) | (r[5] << 8) | r[6]

# # ================= SMOOTH FUNCTION =================
# def smooth(old, new, alpha=0.35):
#     if new is None:
#         return old
#     if old is None:
#         return new
#     return old + alpha * (new - old)

# # ================= LIVE METER =================
# def read_meter():
#     global last_valid, smooth_values

#     vr  = send_and_read(CMD_VOLTAGE_A, 7)
#     ir  = send_and_read(CMD_CURRENT_A, 7)
#     pr  = send_and_read(CMD_POWER_A, 7)
#     pfr = send_and_read(CMD_PF_A, 7)
#     efr = send_and_read(CMD_ENERGY_FWD_OLD, 9)
#     err = send_and_read(CMD_ENERGY_REV_OLD, 9)

#     raw = {
#         "voltage": decode_u16(vr)/100 if vr else None,
#         "current": decode_u16(ir)/100 if ir else None,
#         "power": decode_u16(pr) if pr else None,
#         "pf": decode_u16(pfr)/1000 if pfr else None,
#         "forward_energy": decode_u32(efr)/800 if efr else None,
#         "reverse_energy": decode_u32(err)/800 if err else None,
#     }

#     # 🔥 SMOOTH LIVE VALUES
#     for k in smooth_values:
#         smooth_values[k] = smooth(smooth_values[k], raw[k])

#     last_valid.update(raw)

#     return {
#         **smooth_values,
#         "relay_on": relay_state
#     }

# # ================= FRAMEBUFFER =================
# def draw_box(draw,x,y,w,h,r,fill):
#     draw.rounded_rectangle([x,y,x+w,y+h], radius=r, fill=fill)

# def img_to_rgb565(img):
#     arr = np.array(img, dtype=np.uint16)
#     return ((arr[:,:,0]>>3)<<11)|((arr[:,:,1]>>2)<<5)|(arr[:,:,2]>>3)

# def write_to_fb(img):
#     img = img.convert("RGB")
#     with open(FB_DEV,'wb') as f:
#         f.write(img_to_rgb565(img).tobytes())

# def fmt(v):
#     return "N/A" if v is None else f"{v:.2f}"

# # ================= TOUCH =================
# def get_touch():
#     try:
#         with open("/dev/input/mice", "rb") as f:
#             return (f.read(3)[0] & 1) == 1
#     except:
#         return False

# def handle_touch():
#     global current_page
#     if get_touch():
#         current_page = (current_page + 1) % 2
#         time.sleep(0.25)

# # ================= TERMINAL =================
# def print_debug(m):
#     os.system("clear")
#     print("===== LIVE SMART METER =====")
#     print(f"Voltage : {m['voltage']}")
#     print(f"Current : {m['current']}")
#     print(f"Power   : {m['power']}")
#     print(f"PF      : {m['pf']}")
#     print(f"FWD     : {m['forward_energy']}")
#     print(f"REV     : {m['reverse_energy']}")

# # ================= BLOCKCHAIN =================
# def blockchain_data():
#     return {
#         "prosumer": "PI-1",
#         "consumer": "PI-2",
#         "energy": 2.45,
#         "price": 32.5,
#         "total": 79.6,
#         "status": "WINNER",
#         "tx": "0xA3F9...9BC"
#     }

# # ================= PAGE 1 =================
# def render_meter(m):
#     img = Image.new("RGB",(WIDTH,HEIGHT),BG_COLOR)
#     d = ImageDraw.Draw(img)

#     d.text((20,10),"SMART METER",font=font_small,fill=ACCENT_COLOR)
#     d.text((WIDTH-80,10),"● LIVE",font=font_micro,fill=(0,255,100))

#     items = [
#         ("Power", m["power"]),
#         ("Voltage", m["voltage"]),
#         ("Current", m["current"]),
#         ("PF", m["pf"]),
#         ("FWD", m["forward_energy"]),
#         ("REV", m["reverse_energy"]),
#     ]

#     for i,(k,v) in enumerate(items):
#         x = 20 + (i%2)*220
#         y = 50 + (i//2)*80

#         draw_box(d,x,y,200,70,10,CARD_COLOR)
#         d.text((x+10,y+10),k,font=font_micro,fill=SUBTEXT_COLOR)
#         d.text((x+10,y+30),fmt(v),font=font_small,fill=TEXT_COLOR)

#     return img

# # ================= PAGE 2 =================
# def render_block(b):
#     img = Image.new("RGB",(WIDTH,HEIGHT),BG_COLOR)
#     d = ImageDraw.Draw(img)

#     d.text((20,10),"BLOCKCHAIN",font=font_small,fill=ACCENT_COLOR)
#     d.text((WIDTH-80,10),"● LIVE",font=font_micro,fill=(0,255,100))

#     items = [
#         ("Prosumer", b["prosumer"]),
#         ("Consumer", b["consumer"]),
#         ("Energy", b["energy"]),
#         ("Price", b["price"]),
#         ("Total", b["total"]),
#         ("Status", b["status"]),
#     ]

#     for i,(k,v) in enumerate(items):
#         x = 20 + (i%2)*220
#         y = 50 + (i//2)*80

#         draw_box(d,x,y,200,70,10,CARD_COLOR)
#         d.text((x+10,y+10),k,font=font_micro,fill=SUBTEXT_COLOR)
#         d.text((x+10,y+30),str(v),font=font_small,fill=TEXT_COLOR)

#     return img

# # ================= MAIN LOOP =================
# import os
# import fcntl

# # ================= MAIN LOOP =================
# def main():
#     global current_page

#     load_fonts()

#     last_draw_time = 0
#     last_touch_time = 0
#     REFRESH_RATE = 0.25
#     TOUCH_DEBOUNCE = 0.3

#     # Open mice device ONCE outside loop, set non-blocking
#     try:
#         mice_fd = open("/dev/input/mice", "rb")
#         fcntl.fcntl(mice_fd, fcntl.F_SETFL, os.O_NONBLOCK)
#     except:
#         mice_fd = None

#     while True:
#         now = time.time()

#         # 🔥 ALWAYS READ METER
#         meter = read_meter()
#         block = blockchain_data()

#         # 🖥 ALWAYS PRINT LIVE
#         print_debug(meter)

#         # 👆 TOUCH — non-blocking, won't freeze the loop
#         if mice_fd:
#             try:
#                 data = mice_fd.read(3)
#                 if data and len(data) == 3:
#                     btn = data[0] & 1
#                     if btn and (now - last_touch_time) > TOUCH_DEBOUNCE:
#                         current_page = (current_page + 1) % 2
#                         last_touch_time = now
#             except BlockingIOError:
#                 pass  # No touch data available, skip silently
#             except:
#                 pass

#         # 🔥 TIME-BASED AUTO REFRESH
#         if now - last_draw_time >= REFRESH_RATE:
#             if current_page == 0:
#                 frame = render_meter(meter)
#             else:
#                 frame = render_block(block)

#             write_to_fb(frame)
#             last_draw_time = now

#         time.sleep(0.05)


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         pass
#     finally:
#         ser.close()
#         if mice_fd:
#             mice_fd.close()
#         GPIO.cleanup()
# '''


# def check_paramiko():
#     """Install paramiko if not present."""
#     try:
#         import paramiko
#         return paramiko
#     except ImportError:
#         print("[*] paramiko not found. Installing...")
#         subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
#         import paramiko
#         return paramiko


# def run():
#     paramiko = check_paramiko()

#     print(f"\n{'='*50}")
#     print(f"  Energy Display Remote Runner")
#     print(f"{'='*50}")
#     print(f"  Target : {PI_USER}@{PI_HOST}")
#     print(f"{'='*50}\n")

#     # ── Connect
#     print("[1/5] Connecting to Pi via SSH...")
#     ssh = paramiko.SSHClient()
#     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     try:
#         ssh.connect(PI_HOST, username=PI_USER, password=PI_PASSWORD, timeout=10)
#     except Exception as e:
#         print(f"\n[ERROR] Could not connect: {e}")
#         print("  → Check PI_HOST, PI_USER, PI_PASSWORD at the top of this file.")
#         sys.exit(1)
#     print("       Connected ✓")

#     # ── Upload display code to Pi
#     print("[2/5] Uploading display script to Pi...")
#     sftp = ssh.open_sftp()
#     remote_path = f"/home/{PI_USER}/_energy_display_remote.py"
#     with sftp.open(remote_path, "w") as f:
#         f.write(DISPLAY_CODE)
#     sftp.close()
#     print(f"       Uploaded to {remote_path} ✓")

#     # ── Install dependencies
#     print("[3/5] Installing dependencies on Pi (pillow, numpy)...")
#     _, stdout, stderr = ssh.exec_command(
#         "sudo apt-get install -y python3-numpy python3-pil 2>&1 || "
#         "pip3 install pillow numpy 2>&1"
#     )
#     out = stdout.read().decode()
#     if "error" in out.lower():
#         print(f"       Warning during install: {out[:200]}")
#     else:
#         print("       Dependencies ready ✓")

#     # ── Stop lightdm if running
#     print("[4/5] Stopping display manager on Pi (if running)...")
#     ssh.exec_command("sudo systemctl stop lightdm 2>/dev/null || true")
#     print("       Done ✓")

#     # ── Run the script — stream output live
#     print("[5/5] Running display script on Pi...\n")
#     print("-" * 50)

#     transport = ssh.get_transport()
#     channel   = transport.open_session()
#     channel.get_pty()  # allocate a pseudo-terminal so Ctrl+C works
#     channel.exec_command(f"sudo python3 {remote_path}")

#     try:
#         while True:
#             if channel.recv_ready():
#                 data = channel.recv(1024).decode(errors="replace")
#                 print(data, end="", flush=True)
#             if channel.exit_status_ready():
#                 # drain remaining output
#                 while channel.recv_ready():
#                     print(channel.recv(1024).decode(errors="replace"), end="", flush=True)
#                 break
#     except KeyboardInterrupt:
#         print("\n\n[*] Ctrl+C detected — sending interrupt to Pi...")
#         channel.send(b"\x03")   # send Ctrl+C to remote
#         import time
#         time.sleep(1)
#         while channel.recv_ready():
#             print(channel.recv(1024).decode(errors="replace"), end="", flush=True)

#     channel.close()

#     # ── Cleanup
#     ssh.exec_command(f"rm -f {remote_path}")
#     ssh.close()
#     print("\n" + "-" * 50)
#     print("[✓] Session complete. Connection closed.")


# if __name__ == "__main__":
#     run()


# #!/usr/bin/env python3
"""
P2P Energy Auction — Multi-Pi Launcher
=======================================
Connects to all 6 Pis via SSH and deploys the energy auction + display system.

ROLES:
  Prosumers : 100.120.139.128, 100.80.11.48, 100.120.124.29
  Consumers : 100.76.91.82, 100.93.80.36, 100.71.238.87

Run from YOUR machine:
    python energy_p2p_launcher.py

Optional flags:
    --stop       Stop running instances on all Pis
    --status     Check which Pis are reachable
"""

import subprocess, sys, time, threading, argparse

# ─────────────────────────────────────────────
#  PI CONFIGURATION
# ─────────────────────────────────────────────
PI_PASSWORD = "Lums12345"  # ← same password for all Pis (edit if different)
PI_USER     = "pi"         # ← same username for all Pis (edit if different)




  # {"id": 6, "ip": "100.71.238.87",   "role": "consumer"},
  # {"id": 4, "ip": "100.76.91.82",    "role": "consumer"},
  #     {"id": 1, "ip": "100.120.139.128", "role": "prosumer"},
#     {"id": 2, "ip": "100.80.11.48",    "role": "prosumer"},
PIES = [
    {"id": 3, "ip": "100.120.124.29",  "role": "prosumer"},
    {"id": 5, "ip": "100.93.80.36",    "role": "consumer"}
]

ALL_IPS = [p["ip"] for p in PIES]

# ─────────────────────────────────────────────
#  THE CODE THAT RUNS ON EACH PI
# ─────────────────────────────────────────────
DISPLAY_CODE_TEMPLATE = r'''
# ═══════════════════════════════════════════════════════════════════
#  P2P ENERGY AUCTION NODE  —  Pi #{PI_ID} ({ROLE})
#  Auto-generated by energy_p2p_launcher.py
# ═══════════════════════════════════════════════════════════════════
import serial
import RPi.GPIO as GPIO
import time, os, json, socket, threading, random, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fcntl

# ─── IDENTITY ────────────────────────────────────────────────────
PI_ID   = {PI_ID}
ROLE    = "{ROLE}"   # "prosumer" or "consumer"
MY_IP   = "{MY_IP}"
P2P_PORT = 5555

ALL_PEERS = {ALL_PEERS}   # list of all Pi IPs

# ─── GPIO ────────────────────────────────────────────────────────
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
DE_PIN = 18
GPIO.setup(DE_PIN, GPIO.OUT)
GPIO.output(DE_PIN, GPIO.LOW)

# ─── FRAMEBUFFER ─────────────────────────────────────────────────
FB_DEV = "/dev/fb1"
WIDTH, HEIGHT = 480, 320

# ─── COLORS ──────────────────────────────────────────────────────
BG_COLOR      = (8, 14, 24)
CARD_COLOR    = (18, 28, 42)
CARD2_COLOR   = (14, 24, 38)
ACCENT_COLOR  = (0, 220, 130)
ACCENT2_COLOR = (0, 160, 255)
TEXT_COLOR    = (220, 245, 235)
SUBTEXT_COLOR = (100, 160, 140)
WARN_COLOR    = (255, 130, 50)
WIN_COLOR     = (255, 210, 0)
ROLE_COLOR    = (0, 220, 130) if ROLE == "prosumer" else (0, 160, 255)

# ─── STATE ───────────────────────────────────────────────────────
current_page = 0

smooth_values = {k: None for k in
    ["voltage","current","power","pf","forward_energy","reverse_energy"]}

# Auction state (shared between threads)
auction_lock = threading.Lock()
auction_state = {
    "offers":  {},   # ip -> {energy, price, pi_id}
    "bids":    {},   # ip -> {amount, price, pi_id}
    "trades":  [],   # list of completed trades
    "my_offer": None,
    "my_bid":   None,
    "last_winner": None,
}

blockchain = []   # local chain

# ─── FONTS ───────────────────────────────────────────────────────
def get_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

font_micro = get_font(11)
font_small = get_font(14)
font_med   = get_font(18)
font_large = get_font(26)

# ─── MODBUS ──────────────────────────────────────────────────────
def modbus_crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF

CMD_VOLTAGE_A      = bytes.fromhex("01 03 00 48 00 01 04 1C")
CMD_CURRENT_A      = bytes.fromhex("01 03 00 49 00 01 55 DC")
CMD_POWER_A        = bytes.fromhex("01 03 00 4A 00 01 A5 DC")
CMD_PF_A           = bytes.fromhex("01 03 00 4D 00 01 14 1D")
CMD_ENERGY_FWD_OLD = bytes.fromhex("01 03 00 4B 00 02 B4 1D")
CMD_ENERGY_REV_OLD = bytes.fromhex("01 03 00 4E 00 02 A4 1C")

ser = serial.Serial("/dev/serial0", baudrate=9600, timeout=0.8)

def tx(): GPIO.output(DE_PIN, GPIO.HIGH)
def rx(): GPIO.output(DE_PIN, GPIO.LOW)

def send_and_read(cmd, n):
    ser.reset_input_buffer()
    tx(); ser.write(cmd); ser.flush()
    time.sleep(0.004)
    rx(); time.sleep(0.002)
    resp = ser.read(n)
    if len(resp) != n: return None
    if resp[0] != 1 or resp[1] != 3: return None
    if (resp[-2] | (resp[-1] << 8)) != modbus_crc16(resp[:-2]): return None
    return resp

def decode_u16(r): return (r[3] << 8) | r[4]
def decode_u32(r): return (r[3] << 24) | (r[4] << 16) | (r[5] << 8) | r[6]

def smooth(old, new, alpha=0.35):
    if new is None: return old
    if old is None: return new
    return old + alpha * (new - old)

def read_meter():
    vr  = send_and_read(CMD_VOLTAGE_A, 7)
    ir  = send_and_read(CMD_CURRENT_A, 7)
    pr  = send_and_read(CMD_POWER_A, 7)
    pfr = send_and_read(CMD_PF_A, 7)
    efr = send_and_read(CMD_ENERGY_FWD_OLD, 9)
    err = send_and_read(CMD_ENERGY_REV_OLD, 9)

    raw = {
        "voltage":        decode_u16(vr)/100   if vr  else None,
        "current":        decode_u16(ir)/100   if ir  else None,
        "power":          decode_u16(pr)        if pr  else None,
        "pf":             decode_u16(pfr)/1000  if pfr else None,
        "forward_energy": decode_u32(efr)/800   if efr else None,
        "reverse_energy": decode_u32(err)/800   if err else None,
    }
    for k in smooth_values:
        smooth_values[k] = smooth(smooth_values[k], raw[k])
    return dict(smooth_values)

# ─── P2P NETWORKING ──────────────────────────────────────────────
def send_msg(ip, msg_dict, timeout=2):
    """Send a JSON message to a peer."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, P2P_PORT))
        s.sendall((json.dumps(msg_dict) + "\n").encode())
        s.close()
    except:
        pass

def broadcast(msg_dict):
    """Send message to all peers (not self)."""
    peers = [ip for ip in ALL_PEERS if ip != MY_IP]
    for ip in peers:
        threading.Thread(target=send_msg, args=(ip, msg_dict), daemon=True).start()

def handle_client(conn, addr):
    """Handle an incoming P2P message."""
    try:
        data = b""
        while True:
            chunk = conn.recv(1024)
            if not chunk: break
            data += chunk
        msg = json.loads(data.decode().strip())
        process_message(msg, addr[0])
    except:
        pass
    finally:
        conn.close()

def process_message(msg, from_ip):
    """Route incoming messages to the right handler."""
    t = msg.get("type")
    with auction_lock:
        if t == "OFFER":
            auction_state["offers"][from_ip] = {
                "energy": msg["energy"],
                "price":  msg["price"],
                "pi_id":  msg["pi_id"],
            }
        elif t == "BID":
            auction_state["bids"][from_ip] = {
                "amount": msg["amount"],
                "price":  msg["price"],
                "pi_id":  msg["pi_id"],
            }
        elif t == "TRADE_COMPLETE":
            trade = {
                "prosumer_id": msg["prosumer_id"],
                "consumer_id": msg["consumer_id"],
                "energy":      msg["energy"],
                "price":       msg["price"],
                "total":       msg["total"],
                "tx_hash":     msg["tx_hash"],
                "ts":          msg["ts"],
            }
            auction_state["trades"].append(trade)
            auction_state["last_winner"] = trade
            # Add to local blockchain
            prev_hash = blockchain[-1]["hash"] if blockchain else "0"*64
            block = {**trade, "prev_hash": prev_hash, "index": len(blockchain)}
            block["hash"] = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
            blockchain.append(block)

def server_thread():
    """Listen for incoming P2P connections."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", P2P_PORT))
    srv.listen(10)
    while True:
        try:
            conn, addr = srv.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except:
            break

# ─── AUCTION LOGIC ───────────────────────────────────────────────
def auction_cycle():
    """Run auction rounds every 10 seconds."""
    while True:
        time.sleep(10)

        if ROLE == "prosumer":
            # Prosumer: read surplus and broadcast an offer
            m = smooth_values
            surplus = (m["forward_energy"] or 0) - (m["reverse_energy"] or 0)
            surplus = max(0.01, round(abs(surplus) * 0.1 + random.uniform(0.1, 2.0), 2))
            price   = round(random.uniform(8.0, 18.0), 2)   # PKR/kWh

            offer = {
                "type":   "OFFER",
                "pi_id":  PI_ID,
                "energy": surplus,
                "price":  price,
            }
            with auction_lock:
                auction_state["my_offer"] = offer

            broadcast(offer)
            print(f"[AUCTION] Broadcast OFFER: {surplus} kWh @ PKR {price}")

        elif ROLE == "consumer":
            # Consumer: look at available offers, bid on best (lowest price)
            with auction_lock:
                offers = dict(auction_state["offers"])

            if not offers:
                print("[AUCTION] No offers available yet.")
                continue

            # Pick lowest price offer
            best_ip = min(offers, key=lambda ip: offers[ip]["price"])
            best    = offers[best_ip]
            bid_price = round(best["price"] * random.uniform(0.95, 1.05), 2)
            amount    = round(random.uniform(0.5, best["energy"]), 2)

            bid = {
                "type":   "BID",
                "pi_id":  PI_ID,
                "amount": amount,
                "price":  bid_price,
            }
            with auction_lock:
                auction_state["my_bid"] = bid

            send_msg(best_ip, bid)
            print(f"[AUCTION] Sent BID to Pi-{best['pi_id']}: {amount} kWh @ PKR {bid_price}")

        # Prosumer: settle bids
        if ROLE == "prosumer":
            time.sleep(3)  # wait for bids to arrive
            with auction_lock:
                bids    = dict(auction_state["bids"])
                my_offer = auction_state.get("my_offer")

            if not bids or not my_offer:
                continue

            # Winner: highest bid price
            winner_ip  = max(bids, key=lambda ip: bids[ip]["price"])
            winner_bid = bids[winner_ip]
            energy     = min(winner_bid["amount"], my_offer["energy"])
            price      = winner_bid["price"]
            total      = round(energy * price, 2)

            tx_hash = hashlib.sha256(
                f"{PI_ID}{winner_bid['pi_id']}{energy}{price}{time.time()}".encode()
            ).hexdigest()[:16]

            trade_msg = {
                "type":        "TRADE_COMPLETE",
                "prosumer_id": PI_ID,
                "consumer_id": winner_bid["pi_id"],
                "energy":      energy,
                "price":       price,
                "total":       total,
                "tx_hash":     "0x" + tx_hash,
                "ts":          time.strftime("%H:%M:%S"),
            }

            # Notify all peers and record locally
            broadcast(trade_msg)
            process_message(trade_msg, MY_IP)
            print(f"[AUCTION] TRADE SETTLED → Consumer Pi-{winner_bid['pi_id']} "
                  f"wins {energy} kWh @ PKR {price} | Total: PKR {total}")

            # Clear bids for next round
            with auction_lock:
                auction_state["bids"] = {}

# ─── FRAMEBUFFER DRAWING ─────────────────────────────────────────
def draw_box(draw, x, y, w, h, r, fill):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill)

def img_to_rgb565(img):
    arr = np.array(img, dtype=np.uint16)
    return ((arr[:,:,0]>>3)<<11)|((arr[:,:,1]>>2)<<5)|(arr[:,:,2]>>3)

def write_to_fb(img):
    img = img.convert("RGB")
    with open(FB_DEV, "wb") as f:
        f.write(img_to_rgb565(img).tobytes())

def fmt(v, unit=""):
    if v is None: return "N/A"
    return f"{v:.2f}{unit}"

# ─── PAGE 1: LIVE METER ───────────────────────────────────────────
def render_meter(m):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    d = ImageDraw.Draw(img)

    # Header
    role_label = "PROSUMER" if ROLE == "prosumer" else "CONSUMER"
    d.text((12, 8), f"Pi-{PI_ID}  {role_label}", font=font_small, fill=ROLE_COLOR)
    d.text((WIDTH-90, 8), "● LIVE", font=font_micro, fill=(0, 220, 80))

    items = [
        ("Power",   fmt(m["power"],           " W")),
        ("Voltage", fmt(m["voltage"],          " V")),
        ("Current", fmt(m["current"],          " A")),
        ("PF",      fmt(m["pf"])),
        ("Fwd kWh", fmt(m["forward_energy"],   "")),
        ("Rev kWh", fmt(m["reverse_energy"],   "")),
    ]

    for i, (k, v) in enumerate(items):
        x = 12  + (i % 2) * 234
        y = 45  + (i // 2) * 86
        draw_box(d, x, y, 220, 78, 10, CARD_COLOR)
        d.text((x+10, y+10), k, font=font_micro, fill=SUBTEXT_COLOR)
        d.text((x+10, y+32), v, font=font_med,   fill=TEXT_COLOR)

    return img

# ─── PAGE 2: AUCTION STATUS ───────────────────────────────────────
def render_auction():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    d = ImageDraw.Draw(img)

    d.text((12, 8), f"Pi-{PI_ID}  AUCTION", font=font_small, fill=WIN_COLOR)
    d.text((WIDTH-90, 8), "● P2P", font=font_micro, fill=WIN_COLOR)

    with auction_lock:
        offers  = dict(auction_state["offers"])
        bids    = dict(auction_state["bids"])
        winner  = auction_state.get("last_winner")
        trades  = list(auction_state["trades"])

    # My role status
    if ROLE == "prosumer":
        my = auction_state.get("my_offer")
        status_line = f"Offer: {fmt(my['energy'] if my else None)} kWh @ PKR {fmt(my['price'] if my else None)}"
        peer_label  = "Bids Received"
        peers       = bids
    else:
        my = auction_state.get("my_bid")
        status_line = f"Bid: {fmt(my['amount'] if my else None)} kWh @ PKR {fmt(my['price'] if my else None)}"
        peer_label  = "Live Offers"
        peers       = offers

    draw_box(d, 12, 38, 456, 44, 8, CARD2_COLOR)
    d.text((22, 46), status_line, font=font_small, fill=TEXT_COLOR)

    d.text((12, 92), peer_label, font=font_micro, fill=SUBTEXT_COLOR)
    for i, (ip, info) in enumerate(list(peers.items())[:3]):
        x = 12 + i * 154
        draw_box(d, x, 108, 144, 54, 8, CARD_COLOR)
        pid = info.get("pi_id", "?")
        en  = info.get("energy") or info.get("amount") or 0
        pr  = info.get("price", 0)
        d.text((x+8, y+10) if False else (x+8, 114), f"Pi-{pid}", font=font_micro, fill=ROLE_COLOR)
        d.text((x+8, 126), f"{en:.2f} kWh", font=font_micro, fill=TEXT_COLOR)
        d.text((x+8, 138), f"PKR {pr:.2f}", font=font_micro, fill=WIN_COLOR)

    # Last trade
    if winner:
        draw_box(d, 12, 172, 456, 70, 10, (20, 40, 20))
        d.text((22, 178), "LAST TRADE", font=font_micro, fill=ACCENT_COLOR)
        d.text((22, 192), f"P{winner['prosumer_id']} → C{winner['consumer_id']}  "
                          f"{winner['energy']:.2f} kWh @ PKR {winner['price']:.2f}",
               font=font_small, fill=TEXT_COLOR)
        d.text((22, 214), f"Total: PKR {winner['total']:.2f}   TX: {winner['tx_hash']}",
               font=font_micro, fill=SUBTEXT_COLOR)

    # Trade count
    d.text((12, 252), f"Chain length: {len(blockchain)} blocks", font=font_micro, fill=SUBTEXT_COLOR)

    return img

# ─── PAGE 3: BLOCKCHAIN ───────────────────────────────────────────
def render_blockchain():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    d = ImageDraw.Draw(img)

    d.text((12, 8), f"Pi-{PI_ID}  BLOCKCHAIN", font=font_small, fill=ACCENT2_COLOR)
    d.text((WIDTH-90, 8), f"{len(blockchain)} blks", font=font_micro, fill=SUBTEXT_COLOR)

    recent = blockchain[-3:] if blockchain else []
    for i, blk in enumerate(reversed(recent)):
        y = 42 + i * 90
        draw_box(d, 12, y, 456, 82, 10, CARD_COLOR)
        d.text((22, y+8),  f"Block #{blk['index']}  {blk.get('ts','')}", font=font_micro, fill=ACCENT2_COLOR)
        d.text((22, y+24), f"P{blk['prosumer_id']} → C{blk['consumer_id']}  "
                           f"{blk['energy']:.2f} kWh @ PKR {blk['price']:.2f} = PKR {blk['total']:.2f}",
               font=font_small, fill=TEXT_COLOR)
        d.text((22, y+46), f"TX: {blk['tx_hash']}", font=font_micro, fill=WIN_COLOR)
        d.text((22, y+60), f"Prev: {blk['prev_hash'][:24]}...", font=font_micro, fill=SUBTEXT_COLOR)

    if not blockchain:
        d.text((120, 140), "No trades yet", font=font_med, fill=SUBTEXT_COLOR)

    return img

# ─── TOUCH HANDLING ───────────────────────────────────────────────
def open_mice():
    try:
        fd = open("/dev/input/mice", "rb")
        fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
        return fd
    except:
        return None

# ─── MAIN ────────────────────────────────────────────────────────
def main():
    global current_page

    # Start P2P server
    threading.Thread(target=server_thread, daemon=True).start()
    time.sleep(0.5)
    print(f"[NET] P2P server listening on port {P2P_PORT}")

    # Start auction engine
    threading.Thread(target=auction_cycle, daemon=True).start()
    print(f"[AUCTION] Auction engine started as {ROLE.upper()}")

    mice_fd         = open_mice()
    last_draw_time  = 0
    last_touch_time = 0
    REFRESH_RATE    = 0.25
    TOUCH_DEBOUNCE  = 0.35
    NUM_PAGES       = 3   # meter / auction / blockchain

    while True:
        now = time.time()

        # Read meter
        meter = read_meter()

        # Terminal debug
        os.system("clear")
        print(f"=== Pi-{PI_ID} | {ROLE.upper()} | Page {current_page+1}/{NUM_PAGES} ===")
        print(f"Voltage : {meter['voltage']}  Current: {meter['current']}")
        print(f"Power   : {meter['power']}    PF     : {meter['pf']}")
        print(f"FWD kWh : {meter['forward_energy']}  REV kWh: {meter['reverse_energy']}")
        with auction_lock:
            print(f"Offers  : {len(auction_state['offers'])}   Bids: {len(auction_state['bids'])}")
            print(f"Trades  : {len(auction_state['trades'])}   Chain: {len(blockchain)} blocks")

        # Touch → next page
        if mice_fd:
            try:
                data = mice_fd.read(3)
                if data and len(data) == 3 and (data[0] & 1):
                    if now - last_touch_time > TOUCH_DEBOUNCE:
                        current_page = (current_page + 1) % NUM_PAGES
                        last_touch_time = now
            except BlockingIOError:
                pass
            except:
                pass

        # Render
        if now - last_draw_time >= REFRESH_RATE:
            if current_page == 0:
                frame = render_meter(meter)
            elif current_page == 1:
                frame = render_auction()
            else:
                frame = render_blockchain()

            write_to_fb(frame)
            last_draw_time = now

        time.sleep(0.05)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        GPIO.cleanup()
'''


def check_paramiko():
    try:
        import paramiko
        return paramiko
    except ImportError:
        print("[*] Installing paramiko...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
        import paramiko
        return paramiko


def deploy_pi(pi, paramiko, stop=False):
    """Connect to a single Pi, upload and run (or stop) the node script."""
    ip   = pi["ip"]
    role = pi["role"]
    pid  = pi["id"]
    user = PI_USER
    pw   = PI_PASSWORD

    # Build the all-peers list string for injection into the script
    all_peers_str = str([p["ip"] for p in PIES])

    code = DISPLAY_CODE_TEMPLATE \
        .replace("{PI_ID}",     str(pid)) \
        .replace("{ROLE}",      role) \
        .replace("{MY_IP}",     ip) \
        .replace("{ALL_PEERS}", all_peers_str)

    label = f"Pi-{pid} ({role}) @ {ip}"

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=pw, timeout=10)

        if stop:
            ssh.exec_command("sudo pkill -f _energy_node_remote.py 2>/dev/null; true")
            print(f"  [STOP] {label} ✓")
            ssh.close()
            return

        # Upload
        remote_path = f"/home/{user}/_energy_node_remote.py"
        sftp = ssh.open_sftp()
        with sftp.open(remote_path, "w") as f:
            f.write(code)
        sftp.close()

        # Kill any previous instance
        ssh.exec_command(f"sudo pkill -f {remote_path} 2>/dev/null; true")
        time.sleep(0.5)

        # Install deps (non-blocking, best-effort)
        ssh.exec_command(
            "sudo apt-get install -y python3-numpy python3-pil 2>/dev/null &"
        )

        # Stop display manager
        ssh.exec_command("sudo systemctl stop lightdm 2>/dev/null; true")

        # Launch in background, redirect output to log file
        log = f"/tmp/energy_pi{pid}.log"
        ssh.exec_command(
            f"nohup sudo python3 {remote_path} > {log} 2>&1 &"
        )

        print(f"  [OK]  {label} — launched (log: {log})")
        ssh.close()

    except Exception as e:
        print(f"  [ERR] {label} — {e}")


def status_check(pi, paramiko):
    ip  = pi["ip"]
    pid = pi["id"]
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=PI_USER, password=PI_PASSWORD, timeout=5)
        _, out, _ = ssh.exec_command("pgrep -a python3 | grep _energy_node_remote")
        running = bool(out.read().decode().strip())
        ssh.close()
        status = "RUNNING ✓" if running else "stopped"
        print(f"  Pi-{pid} @ {ip} → {status}")
    except Exception as e:
        print(f"  Pi-{pid} @ {ip} → UNREACHABLE ({e})")


def main():
    parser = argparse.ArgumentParser(description="P2P Energy Auction Launcher")
    parser.add_argument("--stop",   action="store_true", help="Stop all nodes")
    parser.add_argument("--status", action="store_true", help="Check status of all Pis")
    args = parser.parse_args()

    paramiko = check_paramiko()

    print(f"\n{'═'*55}")
    print(f"  P2P Energy Auction — 6-Node Deployment")
    print(f"{'═'*55}")
    for p in PIES:
        print(f"  Pi-{p['id']}  {p['role']:8s}  {p['ip']}")
    print(f"{'═'*55}\n")

    if args.status:
        print("Checking status...\n")
        threads = [
            threading.Thread(target=status_check, args=(p, paramiko))
            for p in PIES
        ]
        for t in threads: t.start()
        for t in threads: t.join()
        return

    action = "STOPPING" if args.stop else "DEPLOYING"
    print(f"{action} all nodes in parallel...\n")

    threads = [
        threading.Thread(target=deploy_pi, args=(p, paramiko, args.stop))
        for p in PIES
    ]
    for t in threads: t.start()
    for t in threads: t.join()

    if not args.stop:
        print(f"\n{'─'*55}")
        print("All nodes deployed. Each Pi is now running autonomously.")
        print("Auction rounds fire every 10 seconds.")
        print("\nUseful commands:")
        print("  python energy_p2p_launcher.py --status   # check all Pis")
        print("  python energy_p2p_launcher.py --stop     # stop all Pis")
        print("  ssh pi@<IP> tail -f /tmp/energy_pi<N>.log  # view logs")
        print(f"{'─'*55}\n")


if __name__ == "__main__":
    main()



