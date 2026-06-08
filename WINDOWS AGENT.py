import time
import requests
import psutil
import ctypes

SERVER = "https://your-render-url.onrender.com"
DEVICE = "pc-01"

start = time.time()

def lock():
    ctypes.windll.user32.LockWorkStation()

while True:

    used = int((time.time() - start) / 60)

    active = "unknown"

    for p in psutil.process_iter(["name"]):
        try:
            active = p.info["name"]
            break
        except:
            pass

    try:
        data = requests.get(SERVER + "/devices").json()
        device = data.get(DEVICE, {})

        limit = device.get("limit", 9999)

        if used >= limit:
            lock()

        requests.post(SERVER + "/update", json={
            "device_id": DEVICE,
            "screen_time": used,
            "active_app": active
        })

    except:
        pass

    time.sleep(5)