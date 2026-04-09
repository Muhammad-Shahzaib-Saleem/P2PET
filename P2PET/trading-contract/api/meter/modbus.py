"""
meter/modbus.py
───────────────
Low-level Modbus RTU layer over RS-485.
Handles GPIO direction control, serial I/O, CRC validation, and byte decoding.
Import nothing from FastAPI – this file is pure hardware logic.
"""

import threading
from typing import Optional

import serial

# ─── GPIO (Raspberry Pi only) ─────────────────────────────────────────────────
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠  RPi.GPIO not found – running in SIMULATION mode.")

# ─── Config ───────────────────────────────────────────────────────────────────
SERIAL_PORT = "/dev/serial0"
BAUD_RATE   = 9600
DE_PIN      = 18     # BCM GPIO pin for DE/RE
TIMEOUT     = 0.3    # serial read timeout in seconds

# ─── Module-level state ───────────────────────────────────────────────────────
_lock: threading.Lock          = threading.Lock()
_ser:  Optional[serial.Serial] = None


# ─── Lifecycle ────────────────────────────────────────────────────────────────

def init() -> None:
    """Open serial port and configure GPIO. Call once at application startup."""
    global _ser
    if not GPIO_AVAILABLE:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DE_PIN, GPIO.OUT)
    GPIO.output(DE_PIN, GPIO.LOW)   # start in RX mode
    _ser = serial.Serial(
        SERIAL_PORT,
        baudrate=BAUD_RATE,
        bytesize=8,
        parity=serial.PARITY_NONE,
        stopbits=1,
        timeout=TIMEOUT,
    )


def cleanup() -> None:
    """Close serial port and release GPIO. Call once at application shutdown."""
    if _ser and _ser.is_open:
        _ser.close()
    if GPIO_AVAILABLE:
        GPIO.cleanup()


# ─── Direction helpers ────────────────────────────────────────────────────────

def _tx() -> None:
    if GPIO_AVAILABLE:
        GPIO.output(DE_PIN, GPIO.HIGH)


def _rx() -> None:
    if GPIO_AVAILABLE:
        GPIO.output(DE_PIN, GPIO.LOW)


# ─── CRC ─────────────────────────────────────────────────────────────────────

def crc16(data: bytes) -> int:
    """Compute Modbus CRC-16."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


# ─── Send / Read ──────────────────────────────────────────────────────────────

def send_and_read(cmd: bytes, expected_len: int) -> Optional[bytes]:
    """
    Transmit *cmd* on the RS-485 bus and read back *expected_len* bytes.

    Returns the validated response bytes, or None on timeout / bad frame / CRC
    error.  Returns None immediately when running without hardware.
    """
    if not GPIO_AVAILABLE or _ser is None:
        return None

    with _lock:
        _ser.reset_input_buffer()
        _ser.reset_output_buffer()
        _tx()
        _ser.write(cmd)
        _ser.flush()
        _rx()
        resp = _ser.read(expected_len)

    if len(resp) != expected_len:
        print(f"[modbus] Short/timeout: got {len(resp)}/{expected_len} bytes  RAW: {resp.hex(' ').upper()}")
        return None

    if resp[0] != 0x01 or resp[1] != 0x03:
        print(f"[modbus] Bad header: {resp.hex(' ').upper()}")
        return None

    crc_rx   = resp[-2] | (resp[-1] << 8)
    crc_calc = crc16(resp[:-2])
    if crc_rx != crc_calc:
        print(f"[modbus] CRC mismatch: got 0x{crc_rx:04X}, calc 0x{crc_calc:04X}  RAW: {resp.hex(' ').upper()}")
        return None

    return resp


# ─── Decoders ─────────────────────────────────────────────────────────────────

def decode_u16(resp: bytes) -> int:
    """Extract a 16-bit unsigned integer from a Modbus read-register response."""
    # frame: [id][func][byte_count][hi][lo][crc_lo][crc_hi]
    return (resp[3] << 8) | resp[4]


def decode_u32(resp: bytes) -> int:
    """Extract a 32-bit unsigned integer from a Modbus read-register response."""
    # frame: [id][func][byte_count][hi1][lo1][hi2][lo2][crc_lo][crc_hi]
    return (resp[3] << 24) | (resp[4] << 16) | (resp[5] << 8) | resp[6]