from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
import time, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Store ─────────────────────────────────────────────────────────────────────
devices: dict = {}

DEFAULT_BLOCKED = [
    "RobloxPlayerBeta.exe", "RobloxPlayer.exe",
    "RiotClientServices.exe", "VALORANT-Win64-Shipping.exe",
    "TLauncher.exe", "TLauncher-2.0.exe",
]

def _ensure(did: str):
    if did not in devices:
        devices[did] = {
            "screen_time": 0, "active_app": "unknown",
            "last_seen": time.time(), "limit": 9999,
            "blocked_apps": list(DEFAULT_BLOCKED),
            "locked": False, "pending_alert": None,
        }

# ── Models ────────────────────────────────────────────────────────────────────
class DeviceUpdate(BaseModel):
    device_id: str
    screen_time: int
    active_app: str = "unknown"

class SetLimit(BaseModel):
    device_id: str
    limit: int

class AppAction(BaseModel):
    device_id: str
    app_name: str

class SetBlockedApps(BaseModel):
    device_id: str
    blocked_apps: List[str]

class AlertMsg(BaseModel):
    device_id: str
    message: str

# ── Agent endpoints ───────────────────────────────────────────────────────────
@app.post("/update")
def update(u: DeviceUpdate):
    _ensure(u.device_id)
    devices[u.device_id].update({
        "screen_time": u.screen_time,
        "active_app":  u.active_app,
        "last_seen":   time.time(),
    })
    return {"ok": True}

@app.get("/commands/{device_id}")
def commands(device_id: str):
    _ensure(device_id)
    dev = devices[device_id]
    alert = dev.get("pending_alert")
    if alert:
        dev["pending_alert"] = None
    return {
        "limit":        dev["limit"],
        "blocked_apps": dev["blocked_apps"],
        "locked":       dev.get("locked", False),
        "alert":        alert,
    }

# ── Dashboard endpoints ───────────────────────────────────────────────────────
@app.get("/devices")
def get_devices():
    now = time.time()
    return {
        did: {**{k:v for k,v in d.items() if k != "pending_alert"},
              "online": (now - d["last_seen"]) < 15}
        for did, d in devices.items()
    }

@app.post("/set_limit")
def set_limit(b: SetLimit):
    _ensure(b.device_id)
    devices[b.device_id]["limit"] = b.limit
    return {"ok": True}

@app.post("/add_blocked_app")
def add_app(b: AppAction):
    _ensure(b.device_id)
    lst = devices[b.device_id]["blocked_apps"]
    if b.app_name not in lst:
        lst.append(b.app_name)
    return {"ok": True, "blocked_apps": lst}

@app.post("/remove_blocked_app")
def remove_app(b: AppAction):
    _ensure(b.device_id)
    devices[b.device_id]["blocked_apps"] = [
        x for x in devices[b.device_id]["blocked_apps"] if x != b.app_name
    ]
    return {"ok": True}

@app.post("/lock")
def lock(b: AppAction):
    _ensure(b.device_id)
    devices[b.device_id]["locked"] = True
    return {"ok": True}

@app.post("/unlock")
def unlock(b: AppAction):
    _ensure(b.device_id)
    devices[b.device_id]["locked"] = False
    devices[b.device_id]["screen_time"] = 0
    return {"ok": True}

@app.post("/alert")
def alert(b: AlertMsg):
    _ensure(b.device_id)
    devices[b.device_id]["pending_alert"] = b.message
    return {"ok": True}

@app.post("/reset_timer")
def reset_timer(b: AppAction):
    _ensure(b.device_id)
    devices[b.device_id]["screen_time"] = 0
    return {"ok": True}

# ── Serve dashboard at / ──────────────────────────────────────────────────────
DASHBOARD = open("dashboard.html").read() if os.path.exists("dashboard.html") else "<h1>dashboard.html not found</h1>"

@app.get("/", response_class=HTMLResponse)
def root():
    return DASHBOARD

@app.get("/ping")
def ping():
    return {"status": "ok", "devices": len(devices)}

# ── Keep-alive for Render free tier ──────────────────────────────────────────
import threading, urllib.request
def _keepalive():
    url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:10000")
    while True:
        time.sleep(240)
        try: urllib.request.urlopen(url + "/ping", timeout=5)
        except: pass
threading.Thread(target=_keepalive, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)