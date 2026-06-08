import time
import requests
import psutil
import ctypes

# =========================
# CONFIG
# =========================
SERVER = "https://your-app.onrender.com"  # 🔴 change this
DEVICE_ID = "child-01"

start_time = time.time()

# =========================
# FUNCTIONS
# =========================
def lock_pc():
    ctypes.windll.user32.LockWorkStation()


def get_active_app():
    """Returns a basic active process (simple version)"""
    try:
        for proc in psutil.process_iter(["name"]):
            return proc.info["name"]
    except:
        return "unknown"


# =========================
# MAIN LOOP
# =========================
while True:

    # -------------------------
    # SCREEN TIME CALCULATION
    # -------------------------
    screen_time = int((time.time() - start_time) / 60)

    active_app = get_active_app()

    # -------------------------
    # SEND DATA TO SERVER
    # -------------------------
    try:
        requests.post(SERVER + "/update", json={
            "device_id": DEVICE_ID,
            "screen_time": screen_time,
            "active_app": active_app
        }, timeout=5)
    except:
        pass

    # -------------------------
    # GET COMMANDS FROM SERVER
    # -------------------------
    try:
        res = requests.get(SERVER + f"/commands/{DEVICE_ID}", timeout=5)
        data = res.json()

        limit = data.get("limit", 9999)
        blocked_apps = data.get("blocked_apps", [])

        # -------------------------
        # ENFORCE SCREEN TIME LIMIT
        # -------------------------
        if screen_time >= limit:
            lock_pc()

        # -------------------------
        # BLOCK APPS
        # -------------------------
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] in blocked_apps:
                    proc.kill()
            except:
                pass

    except:
        pass

    time.sleep(5)