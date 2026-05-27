import socks
import socket
import random

# Улучшение №6: Многоуровневая проксификация (Spyderproxy + Tor)

class ProxyChain:
    def __init__(self, use_tor=True):
        self.spyderproxy = '3kBTM0Ya1FXxA7k:9e3c9b9c-1a11-4022-ad68-111eac0e7e21@budget.spyderproxy.com:11000'
        self.tor_proxy = ('127.0.0.1', 9050) if use_tor else None

    def get_socket(self):
        if self.tor_proxy:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, *self.tor_proxy)
            return s
        else:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.spyderproxy.split('@')[1])  # упрощённо
            return s

# Остальные функции движка прокси не меняются
