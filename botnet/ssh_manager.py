import json
import asyncssh
import asyncio
from utils.logger import log

class SSHManager:
    def __init__(self):
        self.nodes = []
        self.load_nodes()

    def load_nodes(self):
        try:
            with open("ssh_nodes.json", "r") as f:
                self.nodes = json.load(f)
        except:
            self.nodes = []

    def save_nodes(self):
        with open("ssh_nodes.json", "w") as f:
            json.dump(self.nodes, f)

    async def execute(self, host, user, password, command):
        try:
            async with asyncssh.connect(host, username=user, password=password, known_hosts=None) as conn:
                result = await conn.run(command)
                return result.stdout
        except Exception as e:
            log(f"[SSH] Ошибка выполнения на {host}: {e}")
            return None
