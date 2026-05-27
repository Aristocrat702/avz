import socks
import socket
import random
import json
import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from utils.logger import log

class ProxyCollector:
    def __init__(self, sources=None):
        if sources is None:
            with open("avz_settings.json", "r") as f:
                settings = json.load(f)
            self.sources = settings.get("proxy_sources", [])
        else:
            self.sources = sources

    async def fetch_list(self, url):
        proxies = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
                    # Простой парсинг: ищем ip:port в тексте
                    import re
                    matches = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', text)
                    proxies.extend(matches)
        except Exception as e:
            log(f"[ProxyCollector] Ошибка при загрузке {url}: {e}")
        return proxies

    async def check_proxy(self, proxy_str, test_url="http://httpbin.org/ip"):
        try:
            proxy_parts = proxy_str.split(':')
            if len(proxy_parts) != 2:
                return False
            ip, port = proxy_parts
            real_url = f"http://{ip}:{port}"
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, proxy=real_url, timeout=5) as resp:
                    if resp.status == 200:
                        return True
        except:
            pass
        return False

    async def collect_and_check(self, max_workers=200):
        all_proxies = []
        tasks = [self.fetch_list(src) for src in self.sources]
        results = await asyncio.gather(*tasks)
        for lst in results:
            all_proxies.extend(lst)
        # Убираем дубликаты
        all_proxies = list(set(all_proxies))
        log(f"[ProxyCollector] Всего найдено {len(all_proxies)} прокси, начинаю проверку...")
        sem = asyncio.Semaphore(max_workers)
        async def check(p):
            async with sem:
                return p if await self.check_proxy(p) else None
        check_tasks = [check(p) for p in all_proxies]
        live = await asyncio.gather(*check_tasks)
        live = [p for p in live if p is not None]
        log(f"[ProxyCollector] Живых прокси: {len(live)}")
        return live

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.load_proxies()

    def load_proxies(self):
        if os.path.exists("proxy_list.json"):
            try:
                with open("proxy_list.json", "r") as f:
                    self.proxies = json.load(f)
                log(f"[Proxy] Загружено {len(self.proxies)} прокси из файла.")
                return
            except Exception as e:
                log(f"[Proxy] Ошибка загрузки proxy_list.json: {e}")
        # Если файла нет, загружаем Spyderproxy как запасной
        self.proxies = [
            {
                "url": "socks5://3kBTM0Ya1FXxA7k:9e3c9b9c-1a11-4022-ad68-111eac0e7e21@budget.spyderproxy.com:11000",
                "type": "socks5"
            }
        ]
        log("[Proxy] Загружен стандартный Spyderproxy.")

    def get_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index % len(self.proxies)]
        self.current_index += 1
        return proxy.get("url", "")

    def random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies).get("url", "")

    async def refresh_proxies(self):
        collector = ProxyCollector()
        live = await collector.collect_and_check()
        # Преобразуем в формат {'url': 'http://...', 'type': 'http'}
        new_list = []
        for p in live:
            new_list.append({"url": f"http://{p}", "type": "http"})
        # Сохраняем
        with open("proxy_list.json", "w") as f:
            json.dump(new_list, f)
        self.proxies = new_list
        log(f"[Proxy] Обновлено {len(new_list)} живых прокси.")
