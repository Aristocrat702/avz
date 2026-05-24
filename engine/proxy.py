import os, json, time, asyncio, aiohttp, requests, threading, random
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_FILE = "proxies_cache.json"

COUNTRY_COORDS = {
    'RU': (55.75, 37.61), 'US': (38.90, -77.03), 'DE': (52.52, 13.40), 'GB': (51.50, -0.12),
    'FR': (48.85, 2.35), 'NL': (52.37, 4.90), 'CA': (45.41, -75.69), 'JP': (35.68, 139.76),
    'CN': (39.91, 116.39), 'BR': (-15.79, -47.88), 'IN': (28.61, 77.23), 'AU': (-35.28, 149.13),
}

class ProxyManager:
    SOURCES = [
        # ================= КРУПНЕЙШИЕ API =================
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&all=yes",
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&all=yes",
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all",
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all",

        # ================= ЗЕРКАЛА TheSpeedX (900+) =================
        *[f"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http_{i}.txt" for i in range(1, 301)],
        *[f"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5_{i}.txt" for i in range(1, 301)],
        *[f"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4_{i}.txt" for i in range(1, 301)],

        # ================= ОСНОВНЫЕ ПРОВЕРЕННЫЕ СПИСКИ =================
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/https.txt",
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://www.proxy-list.download/api/v1/get?type=https",
        "https://www.proxy-list.download/api/v1/get?type=socks5",
        "https://www.proxy-list.download/api/v1/get?type=socks4",

        # ================= АГРЕГАТОРЫ И ПРОВЕРЕННЫЕ СПИСКИ =================
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
        "https://raw.githubusercontent.com/UserR3X/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/UserR3X/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/socks5.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/socks4.txt",
        "https://raw.githubusercontent.com/proxylist-to/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/proxylist-to/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/B4RC0D3/ProxyLists/master/http.txt",
        "https://raw.githubusercontent.com/B4RC0D3/ProxyLists/master/socks5.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES/master/http.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES/master/socks5.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/free-proxy-list/main/proxy-list/http.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/free-proxy-list/main/proxy-list/socks5.txt",
        "https://raw.githubusercontent.com/iamcihat/Free-Proxy-List/main/proxy/http.txt",
        "https://raw.githubusercontent.com/iamcihat/Free-Proxy-List/main/proxy/socks5.txt",
        "https://raw.githubusercontent.com/alexmon1989/russia_proxy_list/master/http.txt",
        "https://raw.githubusercontent.com/alexmon1989/russia_proxy_list/master/socks5.txt",
        "https://raw.githubusercontent.com/ObcbO/Proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/ObcbO/Proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/chambsanon/ProxyGrab/main/proxies/http.txt",
        "https://raw.githubusercontent.com/chambsanon/ProxyGrab/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list",
        "https://raw.githubusercontent.com/RX402/Proxy-List/main/proxies/http.txt",
        "https://raw.githubusercontent.com/RX402/Proxy-List/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/elliottophellia/yakumo/master/proxies/http.txt",
        "https://raw.githubusercontent.com/elliottophellia/yakumo/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/mertcangokgoz/Proxy-List/main/proxies/http.txt",
        "https://raw.githubusercontent.com/mertcangokgoz/Proxy-List/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks5.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/proxies/http.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/proxies/socks5.txt",

        # ================= МАССИВНОЕ РАСШИРЕНИЕ (2000+) =================
        *[f"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http_{i}.txt" for i in range(301, 1001)],
        *[f"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5_{i}.txt" for i in range(301, 1001)],
        *[f"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4_{i}.txt" for i in range(301, 1001)],

        # Другие проверенные репозитории (полный список)
        "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/http.txt",
        "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/GoekhanDev/free-proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/GoekhanDev/free-proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/GoekhanDev/free-proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/Ian-Lusule/Proxies/main/proxies/http.txt",
        "https://raw.githubusercontent.com/Ian-Lusule/Proxies/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/Ian-Lusule/Proxies/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/Skillter/ProxyGather/master/proxies/working-proxies-http.txt",
        "https://raw.githubusercontent.com/Skillter/ProxyGather/master/proxies/working-proxies-socks4.txt",
        "https://raw.githubusercontent.com/Skillter/ProxyGather/master/proxies/working-proxies-socks5.txt",
        "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/thenasty1337/free-proxy-list/main/data/latest/proxies.txt",
        "https://raw.githubusercontent.com/thenasty1337/free-proxy-list/main/data/latest/types/http/proxies.txt",
        "https://raw.githubusercontent.com/thenasty1337/free-proxy-list/main/data/latest/types/socks4/proxies.txt",
        "https://raw.githubusercontent.com/thenasty1337/free-proxy-list/main/data/latest/types/socks5/proxies.txt",
        "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
        "https://raw.githubusercontent.com/JIH4DHoss4in/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/Blacky1999/proxy-list/main/proxies.txt",
        "https://raw.githubusercontent.com/VolkanSah/Auto-Proxy-Fetcher/refs/heads/main/proxies.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/gfpcom/free-proxy-list/main/list/http.txt",
        "https://raw.githubusercontent.com/gfpcom/free-proxy-list/main/list/socks5.txt",
        "https://raw.githubusercontent.com/gfpcom/free-proxy-list/main/list/socks4.txt",
        "https://raw.githubusercontent.com/andigwandi/free-proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/andigwandi/free-proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/andigwandi/free-proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/Ax0sec/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/Ax0sec/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/Ax0sec/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/B4RC0D3/ProxyLists/master/https.txt",
        "https://raw.githubusercontent.com/B4RC0D3/ProxyLists/master/socks4.txt",
        "https://raw.githubusercontent.com/cyberknight777/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/cyberknight777/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/cyberknight777/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/D4Vinci/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/D4Vinci/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/D4Vinci/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/dproxylist/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/dproxylist/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/dproxylist/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/elliottophellia/yakumo/master/proxies/socks4.txt",
        "https://raw.githubusercontent.com/elliottophellia/yakumo/master/proxies/https.txt",
        "https://raw.githubusercontent.com/fate0/proxylist/master/proxy-socks5.txt",
        "https://raw.githubusercontent.com/fate0/proxylist/master/proxy-http.txt",
        "https://raw.githubusercontent.com/Flakke/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/Flakke/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/Flakke/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/Gimly/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/Gimly/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/Gimly/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/hieucckha/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/hieucckha/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/hieucckha/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/itsyash/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/itsyash/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/itsyash/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/Kwakoid/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/Kwakoid/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/Kwakoid/Proxy-List/master/socks4.txt",
        "https://raw.githubusercontent.com/LeakProxy/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/LeakProxy/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/LeakProxy/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/mertcangokgoz/Proxy-List/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/mertcangokgoz/Proxy-List/main/proxies/https.txt",
        "https://raw.githubusercontent.com/MrSuicideParrot/Free-Proxies/main/proxies/http.txt",
        "https://raw.githubusercontent.com/MrSuicideParrot/Free-Proxies/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/MrSuicideParrot/Free-Proxies/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks4.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks5.txt",
        "https://raw.githubusercontent.com/proxylist-to/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/proxylist-to/proxy-list/main/https.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
        "https://raw.githubusercontent.com/RX402/Proxy-List/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/RX402/Proxy-List/main/proxies/https.txt",
        "https://raw.githubusercontent.com/saisuiu/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/saisuiu/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/saisuiu/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/https.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies/http.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies/socks5.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt",
        "https://raw.githubusercontent.com/UserR3X/proxy-list/main/socks4.txt",
        "https://raw.githubusercontent.com/UserR3X/proxy-list/main/https.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/proxies/socks4.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/proxies/https.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES/master/socks4.txt",
        "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES/master/https.txt",
        "https://raw.githubusercontent.com/zloi-user/hide-my-name-proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hide-my-name-proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/zloi-user/hide-my-name-proxy-list/master/socks4.txt",

        # ================= ФОРУМЫ И САЙТЫ =================
        "https://spys.me/proxy.txt",
        "https://free-proxy-list.net/",
        "https://www.sslproxies.org/",
        "https://www.us-proxy.org/",
        "https://www.socks-proxy.net/",
        "https://hidemy.name/en/proxy-list/",
        "https://proxyscrape.com/free-proxy-list",
        "https://proxy-daily.com/",
        "https://www.proxynova.com/proxy-server-list/",
        "https://www.proxy-list.download/HTTP",
        "https://www.proxy-list.download/HTTPS",
        "https://www.proxy-list.download/SOCKS5",
        "https://www.proxy-list.download/SOCKS4",
    ]
    SOURCES = list(set(SOURCES))

    def __init__(self, log_func=None, progress_callback=None, status_callback=None):
        self.log = log_func or print
        self.progress = progress_callback
        self.status = status_callback
        self.proxies = []
        self.running = False
        self.stop_flag = False
        self.auto_update_active = False
        self.auto_update_thread = None

    def gather(self, speed_limit=2.0, geo_filter="", elite_only=False, fast_mode=False):
        self.running = True
        self.stop_flag = False
        self.proxies.clear()
        raw = {'http': set(), 'socks5': set()}
        total = len(self.SOURCES)
        self.log(f"[*] Сбор из {total} источников...\n")
        with ThreadPoolExecutor(max_workers=120) as ex:
            futures = [ex.submit(self._fetch_source, url) for url in self.SOURCES]
            for i, f in enumerate(as_completed(futures)):
                if self.stop_flag: break
                proto, added = f.result()
                if proto == 'http':
                    raw['http'].update(added)
                elif proto == 'socks5':
                    raw['socks5'].update(added)
                if self.progress: self.progress((i+1)/total * 30)
        self.log(f"[*] Собрано сырых: HTTP={len(raw['http'])}, SOCKS5={len(raw['socks5'])}\n")
        self.log("[*] Асинхронная проверка (600 потоков, таймауты 15с)...\n")
        asyncio.run(self._async_test_all(raw, speed_limit, geo_filter, elite_only, fast_mode))
        self.log(f"[OK] Боевых прокси: {len(self.proxies)}\n")
        self._save_cache()
        if self.status: self.status(f"Прокси: {len(self.proxies)}")
        self.running = False

    def _fetch_source(self, url):
        try:
            r = requests.get(url, timeout=8)
            added = set()
            for line in r.text.splitlines():
                line = line.strip()
                if ":" in line and len(line.split(":")) == 2:
                    added.add(line)
            if 'socks' in url.lower():
                return ('socks5', added)
            return ('http', added)
        except:
            return (None, set())

    async def _async_test_all(self, raw, speed_limit, geo_filter, elite_only, fast_mode):
        proxies_to_test = []
        for p in list(raw['http'])[:5000]:
            proxies_to_test.append((p, 'http'))
        for p in list(raw['socks5'])[:5000]:
            proxies_to_test.append((p, 'socks5'))
        sem = asyncio.Semaphore(600)
        async with aiohttp.ClientSession() as session:
            tasks = [self._async_test_one(session, p, t, speed_limit, geo_filter, elite_only, fast_mode, sem) for p, t in proxies_to_test]
            total = len(tasks)
            for i, coro in enumerate(asyncio.as_completed(tasks)):
                if self.stop_flag: break
                res = await coro
                if res:
                    self.proxies.append(res)
                if self.progress and i % 100 == 0:
                    self.progress(30 + (i+1)/total*70)

    async def _async_test_one(self, session, proxy_str, typ, speed_limit, geo_filter, elite_only, fast_mode, sem):
        async with sem:
            try:
                ip, port = proxy_str.split(':')
                start = time.time()
                proxy_url = f"{'socks5' if typ=='socks5' else 'http'}://{proxy_str}"
                # Увеличили таймаут до 15 секунд
                async with session.get('http://httpbin.org/ip', proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return None
                    elapsed = time.time() - start
                    if elapsed > speed_limit:
                        return None
                    anonymous = 'elite'
                    headers = resp.headers
                    if 'Via' in headers or 'X-Forwarded-For' in headers:
                        anonymous = 'transparent'
                    if elite_only and anonymous != 'elite':
                        return None
                # Пропускаем вторую проверку в быстром режиме или если прокси SOCKS5
                if not fast_mode and typ == 'http':
                    try:
                        async with session.get('http://example.com/', proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=15)) as resp2:
                            if resp2.status != 200:
                                return None
                    except:
                        return None
                country = ''
                if geo_filter:
                    try:
                        geo_resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=3)
                        data = geo_resp.json()
                        country = data.get('countryCode', '')
                        if country != geo_filter:
                            return None
                    except:
                        pass
                score = round(1.0 / max(elapsed, 0.1), 2) + (3 if anonymous == 'elite' else 0)
                return {'ip': ip, 'port': port, 'type': typ, 'speed': round(elapsed, 3),
                        'score': score, 'country': country, 'anonymous': anonymous}
            except:
                return None

    def get_best_proxies(self, n=None, proxy_type=None):
        filtered = self.proxies
        if proxy_type:
            filtered = [p for p in filtered if p['type'] == proxy_type]
        sorted_proxies = sorted(filtered, key=lambda p: p.get('score', 0), reverse=True)
        if n:
            sorted_proxies = sorted_proxies[:n]
        return [f"{p['ip']}:{p['port']}" for p in sorted_proxies]

    def get_map_data(self):
        points = []
        for p in self.proxies:
            country = p.get('country', '')
            if country in COUNTRY_COORDS:
                lat, lon = COUNTRY_COORDS[country]
                lat += random.uniform(-2, 2)
                lon += random.uniform(-2, 2)
                points.append((lat, lon, p.get('score', 0), p['ip']))
        return points

    def _save_cache(self):
        data = {'timestamp': time.time(), 'proxies': self.proxies}
        with open(CACHE_FILE, 'w') as f: json.dump(data, f, indent=2)

    def load_cache(self, max_age=1800):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE) as f:
                    cache = json.load(f)
                if time.time() - cache['timestamp'] < max_age:
                    self.proxies = cache['proxies']
                    self.log(f"[Cache] Загружено {len(self.proxies)} прокси из кэша\n")
                    return True
            except: pass
        return False

    def start_auto_update(self, interval_minutes, speed_limit, geo_filter, elite_only):
        self.auto_update_active = True
        def updater():
            while self.auto_update_active:
                time.sleep(interval_minutes * 60)
                if not self.running: self.gather(speed_limit, geo_filter, elite_only)
        self.auto_update_thread = threading.Thread(target=updater, daemon=True)
        self.auto_update_thread.start()

    def stop_auto_update(self):
        self.auto_update_active = False
        self.stop()