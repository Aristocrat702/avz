import asyncio, json, hashlib, time
from utils.logger import log

class P2PMarket:
    def __init__(self, node_id, kademlia_network):
        self.node_id = node_id
        self.kad = kademlia_network
        self.orders = []

    async def create_sell_order(self, bot_info, price_xmr):
        order = {
            'type': 'sell',
            'bot_id': bot_info['id'],
            'bot_ip': bot_info['ip'],
            'price': price_xmr,
            'seller': self.node_id.hex(),
            'timestamp': time.time()
        }
        self.orders.append(order)
        await self.kad.store(f"order_{bot_info['id']}", json.dumps(order))
        log(f"[P2PMarket] Ордер на продажу {bot_info['id']} за {price_xmr} XMR")

    async def find_orders(self):
        pass

    async def execute_trade(self, order_id):
        # Интеграция с monero-wallet-rpc
        log(f"[P2PMarket] Торговля {order_id} выполнена")
