"""
meter/relay.py
──────────────
Relay control and energy-transfer session logic.

The transfer session:
  1. relay_on()  – energises the relay (starts energy flow)
  2. Polls reverse energy every POLL_INTERVAL seconds in a background thread
  3. When ER_old >= THRESHOLD_REVERSE_ENERGY, calls relay_off() automatically
  4. Session state is exposed via get_status() for the API to query

Change RELAY_PIN and THRESHOLD_REVERSE_ENERGY to match your hardware.
"""

import threading
import time
from typing import Optional
import requests
from meter.modbus import GPIO_AVAILABLE
from meter.registers import read_energy_rev_old

# ─── Config ───────────────────────────────────────────────────────────────────

RELAY_PIN                 = 27       # BCM GPIO pin connected to relay IN
RELAY_ACTIVE_HIGH         = False    # False → LOW turns relay ON (Active LOW)

POLL_INTERVAL             = 1.0      # seconds between energy reads during transfer

# ─── GPIO import (safe) ───────────────────────────────────────────────────────

if GPIO_AVAILABLE:
    import RPi.GPIO as GPIO

# ─── Session state ────────────────────────────────────────────────────────────

_lock = threading.Lock()



_state = {
    "active":             False,
    "relay_on":           False,
    "start_time":         None,
    "end_time":           None,
    "to_start_rev":       None,   # ← add this
    "current_to_rev":     None,   # ← add this
    "current_from_fwd":   None,   # ← add this
    "threshold":          0.0,    # ← add this (was missing, caused KeyError crash)
    "stop_reason":        None,
}

_stop_event   = threading.Event()
_poll_thread: Optional[threading.Thread] = None









def get_reverse_energy(pi_ip: str) -> float:
    r = requests.get(f"http://{pi_ip}:8002/meter/energy", timeout=3)
    data = r.json()
    return data["energy_rev_old_kwh"]

def get_forward_energy(pi_ip: str) -> float:
    r = requests.get(f"http://{pi_ip}:8003/meter/energy", timeout=3)
    data = r.json()
    return data["energy_fwd_old_kwh"]

def set_relay(pi_ip: str, state: bool):
    requests.post(
        f"http://{pi_ip}:8002/relay/set",
        json={"state": state}
    )

# ─── Low-level relay helpers ──────────────────────────────────────────────────

def _relay_setup() -> None:
    """Set up the relay GPIO pin (called once during app startup via modbus.init)."""
    if not GPIO_AVAILABLE:
        return
    # GPIO.setmode already called in modbus.init – just set up the pin
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    # Make sure relay starts OFF
    GPIO.output(RELAY_PIN, GPIO.LOW if RELAY_ACTIVE_HIGH else GPIO.HIGH)


def relay_on():
    GPIO.output(RELAY_PIN, GPIO.LOW)

def relay_off():
    GPIO.output(RELAY_PIN, GPIO.HIGH)


# ─── Background polling thread ────────────────────────────────────────────────


def _monitor_loop(from_pi_ip: str, to_pi_ip: str, transfer_kwh: float):
    try:
        while not _stop_event.is_set():
            to_rev   = get_reverse_energy(to_pi_ip)
            from_fwd = get_forward_energy(from_pi_ip)

            with _lock:
                _state["current_to_rev"]   = to_rev
                _state["current_from_fwd"] = from_fwd
                start_rev = _state["to_start_rev"]   # ← read inside lock

            delivered = to_rev - start_rev            # ← use local var

            if delivered >= transfer_kwh:
                set_relay(to_pi_ip, False)
                with _lock:
                    _state["active"]      = False
                    _state["relay_on"]    = False
                    _state["end_time"]    = time.time()
                    _state["stop_reason"] = "THRESHOLD_REACHED"
                break

            time.sleep(1)

    except Exception as e:
        set_relay(to_pi_ip, False)
        with _lock:
            _state["active"]      = False
            _state["relay_on"]    = False
            _state["stop_reason"] = f"ERROR: {str(e)}"


# ─── Public session API ───────────────────────────────────────────────────────

def start_transfer(from_pi_ip: str, to_pi_ip: str, transfer_kwh: float):
    """
    Start a P2P energy transfer session.
    - Opens relay on TO pi
    - Monitors reverse energy on TO pi
    - Closes relay when transfer_kwh has been delivered
    """
    global _poll_thread

    with _lock:
        if _state["active"]:
            raise RuntimeError("A transfer session is already active")

        # Snapshot starting reverse energy on TO pi
        to_start_rev = get_reverse_energy(to_pi_ip)

        # Reset state
        _state.update({
            "active":           True,
            "relay_on":         True,
            "start_time":       time.time(),
            "end_time":         None,
            "to_start_rev":     to_start_rev,
            "current_to_rev":   to_start_rev,
            "current_from_fwd": None,
            "threshold":        transfer_kwh,
            "stop_reason":      None,
        })

    # Open relay on TO pi
    set_relay(to_pi_ip, True)

    # Start background monitor
    _stop_event.clear()
    _poll_thread = threading.Thread(
        target=_monitor_loop,
        args=(from_pi_ip, to_pi_ip, transfer_kwh),
        daemon=True,
    )
    _poll_thread.start()


def stop_transfer(to_pi_ip: str):
    """Manually abort an active transfer session."""
    _stop_event.set()
    set_relay(to_pi_ip, False)

    with _lock:
        _state["active"]      = False
        _state["relay_on"]    = False
        _state["end_time"]    = time.time()
        _state["stop_reason"] = "manual"


def get_status() -> dict:
    with _lock:
        return dict(_state)



def setup() -> None:
    """Called once at application startup to initialise the relay pin."""
    _relay_setup()
