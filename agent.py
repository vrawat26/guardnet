import time
import requests
import psutil
import ctypes

SERVER = "https://your-render-url.onrender.com"
DEVICE_ID = "child-01"

start = time.time()

def lock():
    ctypes.windll.user32.LockWorkStation()

while True:

    used = int((time.time() - start) / 60)

    # send data
    try:
        requests.post(SERVER + "/update_time", json={
            "device_id": DEVICE_ID,
            "screen_time": used
        })
    except:
        pass

    # get rules
    try:
        cmd = requests.get(SERVER + "/commands").json()

        if used >= cmd["limit_minutes"]:
            lock()

        for p in psutil.process_iter(["name"]):
            try:
                if p.info["name"] in cmd["blocked_apps"]:
                    p.kill()
            except:
                pass

    except:
        pass

    time.sleep(5)