import asyncio, aiohttp, json, os
from utils.logger import log

SOURCES = [
    "https://api.shodan.io/shodan/host/search?key={}&query=port:22,23",
    "https://censys.io/api/v1/search/ipv4?q=services.port:23",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/online/http.txt",
    "https://sunny9577.github.io/proxy-scraper/proxies.txt",
    "https://scans.io/study/sonar.telnet/latest",
    "https://opendata.rapid7.com/sonar.tcp/2024-01-01-1704065600-telnet_23.json.gz"
]

async def fetch_targets():
    """Собирает целевые IP из всех доступных источников"""
    ips = set()
    async with aiohttp.ClientSession() as session:
        for url in SOURCES:
            try:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        import re
                        found = re.findall(r'\d+\.\d+\.\d+\.\d+', text)
                        ips.update(found)
            except Exception as e:
                log(f"[TargetCollector] Ошибка {url}: {e}")
    log(f"[TargetCollector] Собрано {len(ips)} целевых IP")
    return list(ips)[:5000]  # Ограничиваем для скорости
