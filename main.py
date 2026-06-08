from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jose import jwt
import time

app = FastAPI()

SECRET = "CHANGE_THIS_TO_LONG_RANDOM_STRING"

devices = {}

users = {"parent": "1234"}

def token(user):
    return jwt.encode({"user": user}, SECRET, algorithm="HS256")


class Login(BaseModel):
    username: str
    password: str

class Update(BaseModel):
    device_id: str
    screen_time: int
    active_app: str = "unknown"


@app.post("/login")
def login(l: Login):
    if l.username not in users or users[l.username] != l.password:
        raise HTTPException(401, "invalid login")
    return {"token": token(l.username)}


@app.post("/update")
def update(u: Update):
    devices[u.device_id] = {
        "screen_time": u.screen_time,
        "active_app": u.active_app,
        "last_seen": time.time()
    }
    return {"ok": True}


@app.get("/devices")
def get_devices():
    return devices


@app.post("/set_limit")
def set_limit(device_id: str, limit: int):
    if device_id not in devices:
        devices[device_id] = {}
    devices[device_id]["limit"] = limit
    return {"ok": True}