import asyncio, aiohttp, json, os, re
from utils.logger import log

SOURCES = [
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http.txt",
    "https://sunny9577.github.io/proxy-scraper/proxies.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://spys.me/proxy.txt"
]

async def fetch_targets():
    ips = set()
    async with aiohttp.ClientSession() as session:
        for url in SOURCES:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        found = re.findall(r'\d+\.\d+\.\d+\.\d+', text)
                        ips.update(found)
            except Exception as e:
                log(f"[TargetCollector] Ошибка {url}: {e}")
    log(f"[TargetCollector] Собрано {len(ips)} IP")
    return list(ips)
