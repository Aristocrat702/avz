import socks
import socket
import random
import json
import os
from utils.logger import log

class ProxyChain:
    def __init__(self, use_tor=False):
        self.spyderproxy = '3kBTM0Ya1FXxA7k:9e3c9b9c-1a11-4022-ad68-111eac0e7e21@budget.spyderproxy.com:11000'
        self.tor_proxy = ('127.0.0.1', 9050) if use_tor else None

    def get_socket(self):
        if self.tor_proxy:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, *self.tor_proxy)
            return s
        else:
            s = socks.socksocket()
            parts = self.spyderproxy.split('@')
            user_pass = parts[0].split(':')
            host_port = parts[1].split(':')
            s.set_proxy(socks.SOCKS5, host_port[0], int(host_port[1]), username=user_pass[0], password=user_pass[1])
            return s

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
        self.proxies = [
            {
                "type": "socks5",
                "host": "budget.spyderproxy.com",
                "port": 11000,
                "username": "3kBTM0Ya1FXxA7k",
                "password": "9e3c9b9c-1a11-4022-ad68-111eac0e7e21"
            }
        ]
        log("[Proxy] Загружен стандартный Spyderproxy.")

    def get_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index % len(self.proxies)]
        self.current_index += 1
        if proxy["type"] == "socks5":
            return {
                "http": f"socks5://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}",
                "https": f"socks5://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            }
        else:
            return {
                "http": f"{proxy['type']}://{proxy['host']}:{proxy['port']}",
                "https": f"{proxy['type']}://{proxy['host']}:{proxy['port']}"
            }

    def random_proxy(self):
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        if proxy["type"] == "socks5":
            return f"socks5://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        else:
            return f"{proxy['type']}://{proxy['host']}:{proxy['port']}"
