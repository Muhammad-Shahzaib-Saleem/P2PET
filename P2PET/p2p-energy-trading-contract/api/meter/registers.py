"""
meter/registers.py
──────────────────
Modbus register map and high-level read functions for the single-phase meter.

Each read_*() function sends the appropriate command, decodes the raw bytes,
and returns a plain Python float (or None when no hardware is available).
Simulation values are returned automatically when GPIO is unavailable.
"""

import random
from typing import Optional

from meter.modbus import (
    GPIO_AVAILABLE,
    send_and_read,
    decode_u16,
    decode_u32,
)

# ─── Register commands (pre-CRC'd) ────────────────────────────────────────────
#
#  All commands follow Modbus Function 03 (Read Holding Registers):
#    [device_id] [0x03] [reg_hi] [reg_lo] [qty_hi] [qty_lo] [crc_lo] [crc_hi]

CMD_VOLTAGE_A      = bytes.fromhex("010300480001041C")
CMD_CURRENT_A      = bytes.fromhex("01030049000155DC")
CMD_POWER_A        = bytes.fromhex("0103004A0001A5DC")
CMD_PF_A           = bytes.fromhex("0103004D0001141D")

# Energy – old divisor (/800),  registers 0x004B and 0x004E
CMD_ENERGY_FWD_OLD = bytes.fromhex("0103004B0002B41D")
CMD_ENERGY_REV_OLD = bytes.fromhex("0103004E0002A41C")

# Energy – new divisor (/1000), registers 0x0068 and 0x006A
CMD_ENERGY_FWD_NEW = bytes.fromhex("01030068000245D7")
CMD_ENERGY_REV_NEW = bytes.fromhex("0103006A0002E417")


# ─── Simulation helpers ───────────────────────────────────────────────────────

def _sim_voltage()        -> float: return round(random.uniform(218,   242),    2)
def _sim_current()        -> float: return round(random.uniform(0.5,   15.0),   3)
def _sim_power()          -> float: return round(random.uniform(100,   3500),   1)
def _sim_pf()             -> float: return round(random.uniform(0.80,  1.00),   3)
def _sim_energy_fwd_old() -> float: return round(random.uniform(0,     9999),   3)
def _sim_energy_rev_old() -> float: return round(random.uniform(0,     999),    3)
def _sim_energy_fwd_new() -> float: return round(random.uniform(0,     9999),   3)
def _sim_energy_rev_new() -> float: return round(random.uniform(0,     999),    3)


# ─── Public read functions ────────────────────────────────────────────────────

def read_voltage() -> Optional[float]:
    """Return line voltage in Volts, or None on read failure."""
    if not GPIO_AVAILABLE:
        return _sim_voltage()
    resp = send_and_read(CMD_VOLTAGE_A, 7)
    return decode_u16(resp) / 100.0 if resp else None


def read_current() -> Optional[float]:
    """Return line current in Amperes, or None on read failure."""
    if not GPIO_AVAILABLE:
        return _sim_current()
    resp = send_and_read(CMD_CURRENT_A, 7)
    return decode_u16(resp) / 100.0 if resp else None


def read_power() -> Optional[float]:
    """Return active power in Watts, or None on read failure."""
    if not GPIO_AVAILABLE:
        return _sim_power()
    resp = send_and_read(CMD_POWER_A, 7)
    return float(decode_u16(resp)) if resp else None


def read_power_factor() -> Optional[float]:
    """Return power factor (0–1), or None on read failure."""
    if not GPIO_AVAILABLE:
        return _sim_pf()
    resp = send_and_read(CMD_PF_A, 7)
    return decode_u16(resp) / 1000.0 if resp else None


def read_energy_fwd_old() -> Optional[float]:
    """Return forward energy (old register, divisor /800) in kWh."""
    if not GPIO_AVAILABLE:
        return _sim_energy_fwd_old()
    resp = send_and_read(CMD_ENERGY_FWD_OLD, 9)
    return decode_u32(resp) / 800.0 if resp else None


def read_energy_rev_old() -> Optional[float]:
    """Return reverse energy (old register, divisor /800) in kWh."""
    if not GPIO_AVAILABLE:
        return _sim_energy_rev_old()
    resp = send_and_read(CMD_ENERGY_REV_OLD, 9)
    return decode_u32(resp) / 800.0 if resp else None


def read_energy_fwd_new() -> Optional[float]:
    """Return forward energy (new register, divisor /1000) in kWh."""
    if not GPIO_AVAILABLE:
        return _sim_energy_fwd_new()
    resp = send_and_read(CMD_ENERGY_FWD_NEW, 9)
    return decode_u32(resp) / 1000.0 if resp else None


def read_energy_rev_new() -> Optional[float]:
    """Return reverse energy (new register, divisor /1000) in kWh."""
    if not GPIO_AVAILABLE:
        return _sim_energy_rev_new()
    resp = send_and_read(CMD_ENERGY_REV_NEW, 9)
    return decode_u32(resp) / 1000.0 if resp else None