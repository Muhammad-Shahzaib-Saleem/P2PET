"""
main.py
───────
FastAPI application entry point.
All hardware access lives in meter/modbus.py.
All register logic lives in meter/registers.py.
All relay/transfer logic lives in meter/relay.py.
This file contains only the HTTP layer.

Run with:
    python main.py
        or
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import meter.modbus as modbus
import meter.registers as reg
import meter.relay as relay

# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    modbus.init()   # opens serial + configures DE pin
    relay.setup()   # configures relay GPIO pin
    yield
    modbus.cleanup()

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Energy Meter API",
    description="REST API for reading Modbus RS485 single-phase energy meter data",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Response schemas ─────────────────────────────────────────────────────────

class MeterReading(BaseModel):
    voltage_v:           Optional[float] = None
    current_a:           Optional[float] = None
    power_w:             Optional[float] = None
    power_factor:        Optional[float] = None
    energy_fwd_old_kwh:  Optional[float] = None
    energy_rev_old_kwh:  Optional[float] = None
    energy_fwd_new_kwh:  Optional[float] = None
    energy_rev_new_kwh:  Optional[float] = None
    timestamp:           float           = 0.0

class VoltageReading(BaseModel):
    voltage_v: float
    timestamp: float

class CurrentReading(BaseModel):
    current_a: float
    timestamp: float

class PowerReading(BaseModel):
    power_w: float
    timestamp: float

class PowerFactorReading(BaseModel):
    power_factor: float
    timestamp: float

class EnergyReading(BaseModel):
    energy_fwd_old_kwh: Optional[float] = None
    energy_rev_old_kwh: Optional[float] = None
    energy_fwd_new_kwh: Optional[float] = None
    energy_rev_new_kwh: Optional[float] = None
    timestamp: float

class TransferStartRequest(BaseModel):
    threshold_kwh: Optional[float] = None  # override default if provided

class TransferStatusResponse(BaseModel):
    active:           bool
    relay_on:         bool
    start_time:       Optional[float] = None
    end_time:         Optional[float] = None
    start_energy_kwh: Optional[float] = None
    current_energy_kwh: Optional[float] = None
    threshold_kwh:    float
    stop_reason:      Optional[str]   = None


# ─── Meter routes ─────────────────────────────────────────────────────────────

@app.get("/", summary="Health check")
def root():
    return {
        "status": "ok",
        "hardware_available": modbus.GPIO_AVAILABLE,
        "simulation_mode":    not modbus.GPIO_AVAILABLE,
    }


@app.get("/meter/all", response_model=MeterReading, summary="Read all meter values at once")
def read_all():
    ts      = time.time()
    voltage = reg.read_voltage()
    if voltage is None:
        raise HTTPException(status_code=503, detail="Voltage read failed – meter not responding")
    return MeterReading(
        voltage_v          = voltage,
        current_a          = reg.read_current(),
        power_w            = reg.read_power(),
        power_factor       = reg.read_power_factor(),
        energy_fwd_old_kwh = reg.read_energy_fwd_old(),
        energy_rev_old_kwh = reg.read_energy_rev_old(),
        energy_fwd_new_kwh = reg.read_energy_fwd_new(),
        energy_rev_new_kwh = reg.read_energy_rev_new(),
        timestamp          = ts,
    )


@app.get("/meter/voltage", response_model=VoltageReading, summary="Read voltage (V)")
def get_voltage():
    ts  = time.time()
    val = reg.read_voltage()
    if val is None:
        raise HTTPException(status_code=503, detail="Voltage read failed")
    return VoltageReading(voltage_v=val, timestamp=ts)


@app.get("/meter/current", response_model=CurrentReading, summary="Read current (A)")
def get_current():
    ts  = time.time()
    val = reg.read_current()
    if val is None:
        raise HTTPException(status_code=503, detail="Current read failed")
    return CurrentReading(current_a=val, timestamp=ts)


@app.get("/meter/power", response_model=PowerReading, summary="Read active power (W)")
def get_power():
    ts  = time.time()
    val = reg.read_power()
    if val is None:
        raise HTTPException(status_code=503, detail="Power read failed")
    return PowerReading(power_w=val, timestamp=ts)


@app.get("/meter/power-factor", response_model=PowerFactorReading, summary="Read power factor")
def get_power_factor():
    ts  = time.time()
    val = reg.read_power_factor()
    if val is None:
        raise HTTPException(status_code=503, detail="Power factor read failed")
    return PowerFactorReading(power_factor=val, timestamp=ts)


@app.get("/meter/energy", response_model=EnergyReading, summary="Read all energy registers (kWh)")
def get_energy():
    ts = time.time()
    return EnergyReading(
        energy_fwd_old_kwh = reg.read_energy_fwd_old(),
        energy_rev_old_kwh = reg.read_energy_rev_old(),
        energy_fwd_new_kwh = reg.read_energy_fwd_new(),
        energy_rev_new_kwh = reg.read_energy_rev_new(),
        timestamp          = ts,
    )


# ─── Transfer / relay routes ──────────────────────────────────────────────────

@app.post("/transfer/start", response_model=TransferStatusResponse,
          summary="Turn relay ON and start monitoring reverse energy")
def start_transfer(body: TransferStartRequest = TransferStartRequest()):
    """
    Turns the relay ON and begins polling reverse energy (ER_old) every second.
    When ER_old reaches **threshold_kwh** (default: 2.790 kWh hardcoded in relay.py),
    the relay is turned OFF automatically.

    You can optionally pass a custom threshold in the request body:
    ```json
    { "threshold_kwh": 3.5 }
    ```
    """
    try:
        status = relay.start_transfer(threshold=body.threshold_kwh)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return TransferStatusResponse(
        active             = status["active"],
        relay_on           = status["relay_on"],
        start_time         = status["start_time"],
        end_time           = status["end_time"],
        start_energy_kwh   = status["start_energy"],
        current_energy_kwh = status["current_energy"],
        threshold_kwh      = status["threshold"],
        stop_reason        = status["stop_reason"],
    )


@app.post("/transfer/stop", response_model=TransferStatusResponse,
          summary="Manually turn relay OFF and stop the transfer session")
def stop_transfer():
    """Force-stops an active transfer session and turns the relay OFF immediately."""
    status = relay.stop_transfer()
    return TransferStatusResponse(
        active             = status["active"],
        relay_on           = status["relay_on"],
        start_time         = status["start_time"],
        end_time           = status["end_time"],
        start_energy_kwh   = status["start_energy"],
        current_energy_kwh = status["current_energy"],
        threshold_kwh      = status["threshold"],
        stop_reason        = status["stop_reason"],
    )


@app.get("/transfer/status", response_model=TransferStatusResponse,
         summary="Get current transfer session status")
def transfer_status():
    """Returns live status of the relay and ongoing energy transfer session."""
    status = relay.get_status()
    return TransferStatusResponse(
        active             = status["active"],
        relay_on           = status["relay_on"],
        start_time         = status["start_time"],
        end_time           = status["end_time"],
        start_energy_kwh   = status["start_energy"],
        current_energy_kwh = status["current_energy"],
        threshold_kwh      = status["threshold"],
        stop_reason        = status["stop_reason"],
    )


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("meter_api:app", host="0.0.0.0", port=8000, reload=False)