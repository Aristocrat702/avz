import requests
import json
import os
import subprocess
import sys

VPS_HOST = "80.249.146.202"
VPS_PORT = 5000
API_SECRET = "pceeq1s8wv"

def request_improvement(description: str) -> dict:
    """Отправляет запрос на VPS и получает манифест, затем применяет его"""
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

def apply_local_manifest():
    """Если манифест получен, применяет его через update.py"""
    if os.path.exists("manifest.json"):
        result = subprocess.run([sys.executable, "update.py"], capture_output=True, text=True)
        return result.stdout
    return "Манифест не найден"

def check_connection():
    """Проверяет доступность VPS"""
    try:
        resp = requests.get(f"http://{VPS_HOST}:{VPS_PORT}/ping", timeout=5)
        return resp.status_code == 200
    except:
        return False
