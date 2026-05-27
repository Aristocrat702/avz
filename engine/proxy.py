import socks, socket, random, json, os, asyncio, aiohttp, time, threading, re
from bs4 import BeautifulSoup
from utils.logger import log

DEFAULT_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://sunny9577.github.io/proxy-scraper/proxies.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/socks4.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/socks5.txt",
    "https://spys.me/proxy.txt"
]

class ProxyCollector:
    def __init__(self, sources=None):
        if sources is None:
            try:
                with open("avz_settings.json", "r") as f:
                    settings = json.load(f)
                self.sources = settings.get("proxy_sources", DEFAULT_SOURCES)
            except:
                self.sources = DEFAULT_SOURCES
        else:
            self.sources = sources

    async def fetch_list(self, url):
        proxies = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=20) as resp:
                    text = await resp.text()
                    matches = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', text)
                    proxies.extend(matches)
        except Exception as e:
            log(f"[ProxyCollector] Ошибка {url}: {e}", 'warning')
        return proxies

    async def check_proxy(self, proxy_str, test_url="http://httpbin.org/ip"):
        try:
            ip, port = proxy_str.split(':')
            real_url = f"http://{ip}:{port}"
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, proxy=real_url, timeout=8) as resp:
                    if resp.status == 200:
                        return {"url": real_url, "type": "http", "latency": 0}
        except:
            pass
        return None

    async def collect_and_check(self, max_workers=1000):
        all_proxies = []
        tasks = [self.fetch_list(src) for src in self.sources]
        results = await asyncio.gather(*tasks)
        for lst in results:
            all_proxies.extend(lst)
        all_proxies = list(set(all_proxies))
        log(f"[ProxyCollector] Собрано {len(all_proxies)} кандидатов, проверяю...")
        sem = asyncio.Semaphore(max_workers)
        async def check(p):
            async with sem:
                return await self.check_proxy(p)
        check_tasks = [check(p) for p in all_proxies]
        live = await asyncio.gather(*check_tasks)
        live = [p for p in live if p is not None]
        log(f"[ProxyCollector] Живых прокси: {len(live)}")
        return live

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.refresh_interval = 600
        self.load_proxies()
        self.auto_refresh_thread = threading.Thread(target=self._auto_refresh_worker, daemon=True)
        self.auto_refresh_thread.start()

    def load_proxies(self):
        if os.path.exists("proxy_list.json"):
            try:
                with open("proxy_list.json", "r") as f:
                    self.proxies = json.load(f)
                log(f"[Proxy] Загружено {len(self.proxies)} прокси из файла.")
                return
            except Exception as e:
                log(f"[Proxy] Ошибка загрузки: {e}")
        self.proxies = [
            {"url": "socks5://3kBTM0Ya1FXxA7k:9e3c9b9c-1a11-4022-ad68-111eac0e7e21@budget.spyderproxy.com:11000", "type": "socks5"}
        ]
        log("[Proxy] Используется резервный Spyderproxy.")

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
        with open("proxy_list.json", "w") as f:
            json.dump(live, f, indent=2)
        self.proxies = live
        log(f"[Proxy] Обновлено {len(live)} прокси.")

    def _auto_refresh_worker(self):
        while True:
            time.sleep(self.refresh_interval)
            try:
                asyncio.run(self.refresh_proxies())
            except Exception as e:
                log(f"[Proxy] Ошибка автообновления: {e}")
