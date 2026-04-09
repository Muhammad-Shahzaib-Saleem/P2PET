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

from meter.modbus import GPIO_AVAILABLE
from meter.registers import read_energy_rev_old

# ─── Config ───────────────────────────────────────────────────────────────────

RELAY_PIN                 = 17       # BCM GPIO pin connected to relay IN
RELAY_ACTIVE_HIGH         = False    # False → LOW turns relay ON (Active LOW)
THRESHOLD_REVERSE_ENERGY  = 2.790    # kWh – relay trips when ER_old reaches this
POLL_INTERVAL             = 1.0      # seconds between energy reads during transfer

# ─── GPIO import (safe) ───────────────────────────────────────────────────────

if GPIO_AVAILABLE:
    import RPi.GPIO as GPIO

# ─── Session state ────────────────────────────────────────────────────────────

_lock = threading.Lock()

_state = {
    "active":           False,
    "relay_on":         False,
    "start_time":       None,   # float (epoch)
    "end_time":         None,   # float (epoch)
    "start_energy":     None,   # kWh snapshot when session started
    "current_energy":   None,   # kWh last polled value
    "threshold":        THRESHOLD_REVERSE_ENERGY,
    "stop_reason":      None,   # "threshold_reached" | "manual" | "error"
}

_stop_event   = threading.Event()
_poll_thread: Optional[threading.Thread] = None


# ─── Low-level relay helpers ──────────────────────────────────────────────────

def _relay_setup() -> None:
    """Set up the relay GPIO pin (called once during app startup via modbus.init)."""
    if not GPIO_AVAILABLE:
        return
    # GPIO.setmode already called in modbus.init – just set up the pin
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    # Make sure relay starts OFF
    GPIO.output(RELAY_PIN, GPIO.LOW if RELAY_ACTIVE_HIGH else GPIO.HIGH)


def relay_on() -> None:
    """Energise the relay (close the circuit)."""
    if GPIO_AVAILABLE:
        GPIO.output(RELAY_PIN, GPIO.HIGH if RELAY_ACTIVE_HIGH else GPIO.LOW)
    print(f"[relay] ON  (pin {RELAY_PIN})")


def relay_off() -> None:
    """De-energise the relay (open the circuit)."""
    if GPIO_AVAILABLE:
        GPIO.output(RELAY_PIN, GPIO.LOW if RELAY_ACTIVE_HIGH else GPIO.HIGH)
    print(f"[relay] OFF (pin {RELAY_PIN})")


# ─── Background polling thread ────────────────────────────────────────────────

def _monitor_loop(threshold: float) -> None:
    """
    Runs in a daemon thread.
    Polls reverse energy every POLL_INTERVAL seconds.
    Calls relay_off() and stops when energy >= threshold.
    """
    while not _stop_event.is_set():
        er = read_energy_rev_old()

        with _lock:
            _state["current_energy"] = er

        if er is not None:
            print(f"[relay] Monitoring – ER_old = {er:.3f} kWh  (threshold {threshold:.3f} kWh)")
            if er >= threshold:
                relay_off()
                with _lock:
                    _state["active"]      = False
                    _state["relay_on"]    = False
                    _state["end_time"]    = time.time()
                    _state["stop_reason"] = "threshold_reached"
                print(f"[relay] Threshold reached ({er:.3f} >= {threshold:.3f}). Relay OFF.")
                _stop_event.set()
                return
        else:
            print("[relay] Warning: could not read energy during monitoring")

        _stop_event.wait(POLL_INTERVAL)


# ─── Public session API ───────────────────────────────────────────────────────

def start_transfer(threshold: Optional[float] = None) -> dict:
    """
    Turn the relay ON and begin monitoring reverse energy.
    Returns the initial session state dict.
    Raises RuntimeError if a session is already active.
    """
    global _poll_thread

    with _lock:
        if _state["active"]:
            raise RuntimeError("A transfer session is already active.")

    effective_threshold = threshold if threshold is not None else THRESHOLD_REVERSE_ENERGY

    # Reset stop event and state
    _stop_event.clear()

    start_energy = read_energy_rev_old()
    relay_on()

    with _lock:
        _state.update({
            "active":         True,
            "relay_on":       True,
            "start_time":     time.time(),
            "end_time":       None,
            "start_energy":   start_energy,
            "current_energy": start_energy,
            "threshold":      effective_threshold,
            "stop_reason":    None,
        })

    # Start background monitor
    _poll_thread = threading.Thread(
        target=_monitor_loop,
        args=(effective_threshold,),
        daemon=True,
    )
    _poll_thread.start()

    return get_status()


def stop_transfer() -> dict:
    """
    Manually stop an active transfer session and turn the relay OFF.
    """
    _stop_event.set()
    relay_off()

    with _lock:
        _state.update({
            "active":      False,
            "relay_on":    False,
            "end_time":    time.time(),
            "stop_reason": "manual",
        })

    return get_status()


def get_status() -> dict:
    """Return a copy of the current session state (thread-safe)."""
    with _lock:
        return dict(_state)


def setup() -> None:
    """Called once at application startup to initialise the relay pin."""
    _relay_setup()