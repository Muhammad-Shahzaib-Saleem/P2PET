# meter.py
import serial
import time
import RPi.GPIO as GPIO

# ---------------- CRC ----------------

def modbus_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF

# ---------------- MODBUS COMMANDS ----------------

CMD_ENERGY_FWD = bytes.fromhex("01 03 00 4B 00 02 B4 1D")  # import
CMD_ENERGY_REV = bytes.fromhex("01 03 00 4E 00 02 A4 1C")  # export

ENERGY_DIVISOR = 800.0

# ---------------- RS485 ----------------

DE_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(DE_PIN, GPIO.OUT)
GPIO.output(DE_PIN, GPIO.LOW)

ser = serial.Serial(
    "/dev/serial0",
    baudrate=9600,
    timeout=0.6
)

def tx():
    GPIO.output(DE_PIN, GPIO.HIGH)

def rx():
    GPIO.output(DE_PIN, GPIO.LOW)

# ---------------- MODBUS READ ----------------

def send_and_read(cmd: bytes, expected_len: int):
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    tx()
    ser.write(cmd)
    ser.flush()
    time.sleep(0.003)
    rx()
    time.sleep(0.002)

    resp = ser.read(expected_len)
    if len(resp) != expected_len:
        return None

    if resp[0] != 0x01 or resp[1] != 0x03:
        return None

    crc_rx = resp[-2] | (resp[-1] << 8)
    if crc_rx != modbus_crc16(resp[:-2]):
        return None

    return resp

# ---------------- DECODE ----------------

def decode_u32(resp: bytes) -> int:
    return (resp[3] << 24) | (resp[4] << 16) | (resp[5] << 8) | resp[6]

# ---------------- PUBLIC API ----------------

def read_import_energy():
    resp = send_and_read(CMD_ENERGY_FWD, 9)
    return decode_u32(resp) / ENERGY_DIVISOR if resp else None

def read_export_energy():
    resp = send_and_read(CMD_ENERGY_REV, 9)
    return decode_u32(resp) / ENERGY_DIVISOR if resp else None
