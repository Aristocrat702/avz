import asyncio
import hashlib
import json
import random
import socket
from utils.logger import log

class KademliaNode:
    def __init__(self, port=8468):
        self.node_id = hashlib.sha1(str(random.getrandbits(256)).encode()).digest()
        self.port = port
        self.routing_table = {}  # distance -> (ip, port, node_id)
        self.data_store = {}
        self.server = None

    async def listen(self):
        self.server = await asyncio.start_server(self.handle_connection, '0.0.0.0', self.port)
        log(f"[Kademlia] Узел слушает порт {self.port}")

    async def handle_connection(self, reader, writer):
        try:
            data = await reader.read(4096)
            msg = json.loads(data.decode())
            cmd = msg.get('cmd')
            if cmd == 'ping':
                response = {'cmd': 'pong', 'node_id': self.node_id.hex()}
                writer.write(json.dumps(response).encode())
                await writer.drain()
                # Обновляем таблицу маршрутизации
                sender_id = bytes.fromhex(msg['node_id'])
                sender_addr = writer.get_extra_info('peername')
                distance = int.from_bytes(
                    hashlib.sha1(self.node_id).digest(), 'big'
                ) ^ int.from_bytes(hashlib.sha1(sender_id).digest(), 'big')
                self.routing_table[distance] = (sender_addr[0], sender_addr[1], sender_id)
            elif cmd == 'find_node':
                target_id = bytes.fromhex(msg['target_id'])
                # Возвращаем ближайших узлов из нашей таблицы
                nearest = self._find_k_nearest(target_id, k=3)
                response = {'cmd': 'found_nodes', 'nodes': []}
                for dist, (ip, port, node_id) in nearest:
                    response['nodes'].append({'ip': ip, 'port': port, 'node_id': node_id.hex()})
                writer.write(json.dumps(response).encode())
                await writer.drain()
            elif cmd == 'store':
                key = msg['key']
                value = msg['value']
                self.data_store[key] = value
                writer.write(json.dumps({'cmd': 'stored'}).encode())
                await writer.drain()
            elif cmd == 'find_value':
                key = msg['key']
                if key in self.data_store:
                    writer.write(json.dumps({'cmd': 'value', 'value': self.data_store[key]}).encode())
                else:
                    # Ищем ближайших и возвращаем их
                    target_id = bytes.fromhex(key)
                    nearest = self._find_k_nearest(target_id, k=3)
                    response = {'cmd': 'found_nodes', 'nodes': []}
                    for dist, (ip, port, node_id) in nearest:
                        response['nodes'].append({'ip': ip, 'port': port, 'node_id': node_id.hex()})
                    writer.write(json.dumps(response).encode())
                await writer.drain()
        except Exception as e:
            log(f"[Kademlia] Ошибка обработки: {e}")
        finally:
            writer.close()

    def _find_k_nearest(self, target_id, k=3):
        # Вычисляем XOR расстояние от target_id до всех узлов в таблице
        target_int = int.from_bytes(hashlib.sha1(target_id).digest(), 'big')
        sorted_nodes = []
        for dist, node_info in self.routing_table.items():
            node_id = node_info[2]
            node_int = int.from_bytes(hashlib.sha1(node_id).digest(), 'big')
            distance = target_int ^ node_int
            sorted_nodes.append((distance, node_info))
        sorted_nodes.sort(key=lambda x: x[0])
        return sorted_nodes[:k]

    async def bootstrap(self, bootstrap_host, bootstrap_port):
        try:
            reader, writer = await asyncio.open_connection(bootstrap_host, bootstrap_port)
            msg = json.dumps({'cmd': 'ping', 'node_id': self.node_id.hex()})
            writer.write(msg.encode())
            await writer.drain()
            data = await reader.read(4096)
            writer.close()
            log(f"[Kademlia] Bootstrap успешно к {bootstrap_host}:{bootstrap_port}")
        except Exception as e:
            log(f"[Kademlia] Bootstrap ошибка: {e}")

    async def send_find_node(self, target_node_ip, target_node_port, target_id_hex):
        try:
            reader, writer = await asyncio.open_connection(target_node_ip, target_node_port)
            msg = json.dumps({
                'cmd': 'find_node',
                'target_id': target_id_hex
            })
            writer.write(msg.encode())
            await writer.drain()
            data = await reader.read(4096)
            writer.close()
            return json.loads(data.decode())
        except Exception as e:
            log(f"[Kademlia] find_node ошибка: {e}")
            return None

    async def broadcast_to_network(self, message):
        """Рассылает сообщение всем узлам в таблице маршрутизации"""
        for dist, (ip, port, node_id) in self.routing_table.items():
            try:
                reader, writer = await asyncio.open_connection(ip, port)
                writer.write(json.dumps(message).encode())
                await writer.drain()
                writer.close()
            except Exception as e:
                log(f"[Kademlia] Ошибка отправки {ip}:{port}: {e}")
