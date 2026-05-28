import requests
import json
import os
import subprocess
import sys

VPS_HOST = "80.249.146.202"
VPS_PORT = 5000
API_SECRET = "pceeq1s8wv"

def request_improvement(description: str) -> dict:
    url = f"http://{VPS_HOST}:{VPS_PORT}/improve"
    payload = {
        "description": description,
        "secret": API_SECRET
    }
    try:
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()
        return {"status": "error", "message": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_connection():
    try:
        resp = requests.get(f"http://{VPS_HOST}:{VPS_PORT}/ping", timeout=5)
        return resp.status_code == 200
    except:
        return False
