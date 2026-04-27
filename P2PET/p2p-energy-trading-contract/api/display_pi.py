
import time
import os
import fcntl
import threading

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════════════════
#  CONFIG — edit these to match your setup
# ═══════════════════════════════════════════════════════════════════

API_BASE    = "http://100.93.80.36:8002"   # change port if needed
FB_DEV      = "/dev/fb1"
WIDTH       = 480
HEIGHT      = 320
REFRESH_HZ  = 4          # screen redraws per second
API_HZ      = 2          # API polls per second  (must be ≤ REFRESH_HZ)

# ═══════════════════════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════════════════════

BG_COLOR      = (10,  18,  28)
CARD_COLOR    = (20,  32,  48)
CARD2_COLOR   = (16,  28,  44)
ACCENT_COLOR  = (0,   210, 140)
ACCENT2_COLOR = (0,   140, 255)
TEXT_COLOR    = (230, 255, 245)
SUBTEXT_COLOR = (100, 160, 140)
WARN_COLOR    = (255, 160,  60)
DANGER_COLOR  = (255,  70,  70)
DIM_COLOR     = (40,   60,  80)

# ═══════════════════════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════════════════════

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

def load_font(size):
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

F_TINY   = load_font(10)
F_SMALL  = load_font(13)
F_MED    = load_font(17)
F_LARGE  = load_font(24)
F_TITLE  = load_font(14)

# ═══════════════════════════════════════════════════════════════════
#  STATE  (updated by background thread)
# ═══════════════════════════════════════════════════════════════════

_lock  = threading.Lock()
_state = {
    "meter":    None,   # dict from /meter/all
    "transfer": None,   # dict from /transfer/status
    "sim":      False,  # True when GPIO not available
    "online":   False,
    "err":      "",
    "ts":       0.0,
}

# smooth display values (avoids jumpy numbers)
_smooth = {}

def _smooth_val(key, new, alpha=0.3):
    old = _smooth.get(key)
    if new is None:
        return old
    if old is None:
        _smooth[key] = new
        return new
    val = old + alpha * (new - old)
    _smooth[key] = val
    return val

# ═══════════════════════════════════════════════════════════════════
#  API FETCH THREAD
# ═══════════════════════════════════════════════════════════════════

def _fetch_loop():
    sess = requests.Session()
    while True:
        try:
            m  = sess.get(f"{API_BASE}/meter/all",       timeout=2).json()
            t  = sess.get(f"{API_BASE}/transfer/status", timeout=2).json()
            h  = sess.get(f"{API_BASE}/",                timeout=2).json()
            with _lock:
                _state["meter"]   = m
                _state["transfer"]= t
                _state["sim"]     = h.get("simulation_mode", False)
                _state["online"]  = True
                _state["err"]     = ""
                _state["ts"]      = time.time()
        except Exception as e:
            with _lock:
                _state["online"] = False
                _state["err"]    = str(e)[:48]
        time.sleep(1.0 / API_HZ)

# ═══════════════════════════════════════════════════════════════════
#  FRAMEBUFFER WRITER
# ═══════════════════════════════════════════════════════════════════

def _to_rgb565(img):
    a = np.array(img.convert("RGB"), dtype=np.uint16)
    return (((a[:,:,0] >> 3) << 11) |
            ((a[:,:,1] >> 2) <<  5) |
             (a[:,:,2] >> 3)).tobytes()

def write_fb(img):
    try:
        with open(FB_DEV, "wb") as f:
            f.write(_to_rgb565(img))
    except Exception as e:
        print(f"[FB] write error: {e}")

# ═══════════════════════════════════════════════════════════════════
#  DRAWING HELPERS
# ═══════════════════════════════════════════════════════════════════

def box(d, x, y, w, h, r=8, fill=CARD_COLOR, outline=None):
    d.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill,
                         outline=outline or fill)

def bar(d, x, y, w, h, pct, color):
    """Draw a thin progress bar."""
    d.rounded_rectangle([x, y, x+w, y+h], radius=2, fill=DIM_COLOR)
    fill_w = max(2, int(w * min(pct, 1.0)))
    d.rounded_rectangle([x, y, x+fill_w, y+h], radius=2, fill=color)

def txt(d, x, y, s, font, fill, anchor="la"):
    d.text((x, y), s, font=font, fill=fill, anchor=anchor)

def fmt(v, dec=2, unit=""):
    if v is None:
        return "—"
    return f"{v:.{dec}f}{unit}"

# ═══════════════════════════════════════════════════════════════════
#  PAGE 0 — METER  (electrical readings)
# ═══════════════════════════════════════════════════════════════════

def page_meter(m, sim):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    d   = ImageDraw.Draw(img)

    # ── header ──────────────────────────────────────────────────────
    d.rectangle([0, 0, WIDTH, 32], fill=(14, 24, 38))
    txt(d, 14, 8,  "SMART METER",  F_TITLE, ACCENT_COLOR)
    txt(d, 14, 20, "live readings", F_TINY, SUBTEXT_COLOR)
    status_col = ACCENT_COLOR if not sim else WARN_COLOR
    status_lbl = "● LIVE" if not sim else "◆ SIM"
    txt(d, WIDTH-60, 12, status_lbl, F_SMALL, status_col)
    txt(d, WIDTH-60, 22, time.strftime("%H:%M:%S"), F_TINY, SUBTEXT_COLOR)

    if m is None:
        txt(d, WIDTH//2, HEIGHT//2, "Waiting for data...", F_MED, SUBTEXT_COLOR, "mm")
        return img

    V  = _smooth_val("voltage", m.get("voltage_v"))
    I  = _smooth_val("current", m.get("current_a"))
    P  = _smooth_val("power",   m.get("power_w"))
    PF = _smooth_val("pf",      m.get("power_factor"))

    # ── 4 electrical cards  (2×2 grid) ──────────────────────────────
    cards = [
        ("VOLTAGE",      fmt(V, 1),  "V",    V,  260, ACCENT2_COLOR),
        ("CURRENT",      fmt(I, 2),  "A",    I,   20, ACCENT_COLOR),
        ("ACTIVE POWER", fmt(P, 0),  "W",    P, 5000, WARN_COLOR),
        ("POWER FACTOR", fmt(PF, 3), "",    PF,    1, (180, 130, 255)),
    ]
    CW, CH = 222, 76
    for i, (label, val, unit, raw, mx, col) in enumerate(cards):
        cx = 6  + (i % 2) * (CW + 6)
        cy = 38 + (i // 2) * (CH + 6)
        box(d, cx, cy, CW, CH, r=8, fill=CARD_COLOR)
        txt(d, cx+10, cy+8,  label,        F_TINY,  SUBTEXT_COLOR)
        txt(d, cx+10, cy+26, val,          F_LARGE, TEXT_COLOR)
        if unit:
            txt(d, cx+10+d.textlength(val, font=F_LARGE)+4,
                cy+34, unit, F_SMALL, SUBTEXT_COLOR)
        pct_val = min(1.0, (raw or 0) / mx) if mx else 0
        bar(d, cx+10, cy+CH-14, CW-20, 4, pct_val, col)

    # ── energy row  ─────────────────────────────────────────────────
    EW = (WIDTH - 18) // 4
    energy_items = [
        ("FWD OLD", m.get("energy_fwd_old_kwh"), ACCENT_COLOR),
        ("REV OLD", m.get("energy_rev_old_kwh"), ACCENT2_COLOR),
        ("FWD NEW", m.get("energy_fwd_new_kwh"), ACCENT_COLOR),
        ("REV NEW", m.get("energy_rev_new_kwh"), ACCENT2_COLOR),
    ]
    ey = 38 + 2*(CH+6) + 4
    for i, (lbl, val, col) in enumerate(energy_items):
        ex = 6 + i * (EW + 2)
        box(d, ex, ey, EW, 44, r=6, fill=CARD2_COLOR)
        txt(d, ex+6, ey+4,  lbl,           F_TINY,  SUBTEXT_COLOR)
        txt(d, ex+6, ey+18, fmt(val, 3),   F_SMALL, col)
        txt(d, ex+6, ey+34, "kWh",         F_TINY,  DIM_COLOR)

    return img

# ═══════════════════════════════════════════════════════════════════
#  PAGE 1 — TRANSFER / RELAY
# ═══════════════════════════════════════════════════════════════════

def page_transfer(t, m):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    d   = ImageDraw.Draw(img)

    # ── header ──────────────────────────────────────────────────────
    d.rectangle([0, 0, WIDTH, 32], fill=(14, 24, 38))
    txt(d, 14, 8,  "ENERGY TRANSFER", F_TITLE, ACCENT_COLOR)
    txt(d, 14, 20, "relay & session", F_TINY, SUBTEXT_COLOR)
    txt(d, WIDTH-60, 12, time.strftime("%H:%M:%S"), F_SMALL, SUBTEXT_COLOR)

    if t is None:
        txt(d, WIDTH//2, HEIGHT//2, "No transfer data", F_MED, SUBTEXT_COLOR, "mm")
        return img

    relay_on = t.get("relay_on", False)
    active   = t.get("active",   False)

    # ── relay status card ────────────────────────────────────────────
    relay_col  = ACCENT_COLOR if relay_on else DANGER_COLOR
    relay_lbl  = "RELAY ON" if relay_on else "RELAY OFF"
    box(d, 6, 38, 220, 72, fill=CARD_COLOR)
    # big status dot
    dot_col = ACCENT_COLOR if relay_on else DANGER_COLOR
    d.ellipse([16, 54, 36, 74], fill=dot_col)
    txt(d, 46, 46, relay_lbl, F_MED,   relay_col)
    txt(d, 46, 68, "Active" if active else "Idle", F_SMALL, SUBTEXT_COLOR)

    # ── session info card ────────────────────────────────────────────
    box(d, 234, 38, 240, 72, fill=CARD_COLOR)
    thresh  = t.get("threshold_kwh")
    s_en    = t.get("start_energy_kwh")
    c_en    = t.get("current_energy_kwh")
    txt(d, 244, 42, "THRESHOLD",  F_TINY, SUBTEXT_COLOR)
    txt(d, 244, 54, fmt(thresh, 3, " kWh"), F_MED, TEXT_COLOR)
    txt(d, 244, 76, "STOP REASON: " + (t.get("stop_reason") or "—"), F_TINY, SUBTEXT_COLOR)
    txt(d, 244, 88, f"start {fmt(s_en,3)}  now {fmt(c_en,3)} kWh", F_TINY, DIM_COLOR)

    # ── progress bar ─────────────────────────────────────────────────
    if active and thresh and s_en is not None and c_en is not None:
        delta   = max(0, c_en - s_en)
        pct_val = min(1.0, delta / thresh) if thresh else 0
        box(d, 6, 118, WIDTH-12, 36, fill=CARD2_COLOR)
        txt(d, 14, 122, "TRANSFER PROGRESS", F_TINY, SUBTEXT_COLOR)
        bar(d, 14, 136, WIDTH-28, 8, pct_val, ACCENT_COLOR)
        pct_str = f"{pct_val*100:.1f}%"
        txt(d, WIDTH-18, 134, pct_str, F_TINY, ACCENT_COLOR, anchor="ra")
    else:
        box(d, 6, 118, WIDTH-12, 36, fill=CARD2_COLOR)
        txt(d, WIDTH//2, 136, "No active transfer session", F_SMALL, DIM_COLOR, "mm")

    # ── power snapshot (from /meter/all) ────────────────────────────
    if m:
        V = _smooth.get("voltage") or m.get("voltage_v")
        I = _smooth.get("current") or m.get("current_a")
        P = _smooth.get("power")   or m.get("power_w")
        snap = [
            ("V",   fmt(V, 1), ACCENT2_COLOR),
            ("A",   fmt(I, 2), ACCENT_COLOR),
            ("W",   fmt(P, 0), WARN_COLOR),
        ]
        SW = (WIDTH - 18) // 3
        sy = 162
        for i, (unit, val, col) in enumerate(snap):
            sx = 6 + i * (SW + 3)
            box(d, sx, sy, SW, 52, fill=CARD_COLOR)
            txt(d, sx+8, sy+6,  unit, F_TINY,  SUBTEXT_COLOR)
            txt(d, sx+8, sy+20, val,  F_MED,   col)

    # ── time info ────────────────────────────────────────────────────
    st = t.get("start_time")
    et = t.get("end_time")
    sy2 = 222
    box(d, 6, sy2, WIDTH-12, 42, fill=CARD2_COLOR)
    s_str = time.strftime("%H:%M:%S", time.localtime(st)) if st else "—"
    e_str = time.strftime("%H:%M:%S", time.localtime(et)) if et else "—"
    txt(d, 14, sy2+6,  f"START  {s_str}", F_SMALL, SUBTEXT_COLOR)
    txt(d, 14, sy2+22, f"END    {e_str}", F_SMALL, SUBTEXT_COLOR)

    # ── touch hint ───────────────────────────────────────────────────
    txt(d, WIDTH//2, HEIGHT-8, "tap to switch page", F_TINY, DIM_COLOR, "mb")

    return img

# ═══════════════════════════════════════════════════════════════════
#  OFFLINE SCREEN
# ═══════════════════════════════════════════════════════════════════

def page_offline(err):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    d   = ImageDraw.Draw(img)
    d.rectangle([0, 0, WIDTH, 32], fill=(14, 24, 38))
    txt(d, 14, 10, "P2PET ENERGY MONITOR", F_TITLE, ACCENT_COLOR)
    txt(d, WIDTH//2, HEIGHT//2 - 20, "API OFFLINE", F_LARGE, DANGER_COLOR, "mm")
    txt(d, WIDTH//2, HEIGHT//2 + 10, API_BASE,      F_SMALL, SUBTEXT_COLOR, "mm")
    txt(d, WIDTH//2, HEIGHT//2 + 28, err,           F_TINY,  DIM_COLOR, "mm")
    txt(d, WIDTH//2, HEIGHT//2 + 46, "retrying...", F_TINY,  DIM_COLOR, "mm")
    return img

# ═══════════════════════════════════════════════════════════════════
#  TOUCH INPUT  (non-blocking)
# ═══════════════════════════════════════════════════════════════════

def open_touch():
    try:
        fd = open("/dev/input/mice", "rb")
        fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
        return fd
    except Exception:
        return None

def check_touch(fd, last_t, debounce=0.3):
    if fd is None:
        return False, last_t
    try:
        data = fd.read(3)
        if data and len(data) == 3 and (data[0] & 1):
            now = time.time()
            if now - last_t > debounce:
                return True, now
    except BlockingIOError:
        pass
    except Exception:
        pass
    return False, last_t

# ═══════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════

def main():
    print(f"[display] Starting — API: {API_BASE}  FB: {FB_DEV}  {WIDTH}×{HEIGHT}")

    # Start background fetch thread
    t = threading.Thread(target=_fetch_loop, daemon=True)
    t.start()

    touch_fd  = open_touch()
    page      = 0
    last_touch = 0.0
    frame_dt  = 1.0 / REFRESH_HZ

    while True:
        t0 = time.time()

        # read state snapshot
        with _lock:
            online   = _state["online"]
            meter    = _state["meter"]
            transfer = _state["transfer"]
            sim      = _state["sim"]
            err      = _state["err"]

        # touch → switch page
        tapped, last_touch = check_touch(touch_fd, last_touch)
        if tapped:
            page = (page + 1) % 2
            print(f"[display] page → {page}")

        # render
        if not online:
            frame = page_offline(err)
        elif page == 0:
            frame = page_meter(meter, sim)
        else:
            frame = page_transfer(transfer, meter)

        write_fb(frame)

        # debug print
        if meter:
            print(
                f"[display] p{page} | "
                f"V={fmt(meter.get('voltage_v'),1)} "
                f"I={fmt(meter.get('current_a'),2)} "
                f"P={fmt(meter.get('power_w'),0)}W | "
                f"{'SIM' if sim else 'HW'}"
            )

        # pace to target refresh rate
        elapsed = time.time() - t0
        time.sleep(max(0, frame_dt - elapsed))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[display] Stopped.")
    finally:
        print("[display] Bye.")

