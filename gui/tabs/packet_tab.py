import tkinter as tk
from tkinter import ttk, messagebox
from scapy.all import IP, TCP, send
import threading, asyncio
from utils.logger import log

class PacketTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Конструктор пакетов", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        ttk.Label(main_frame, text="Цель:").pack(anchor=tk.W, pady=2)
        self.target_entry = ttk.Entry(main_frame, width=30)
        self.target_entry.pack()
        
        ttk.Label(main_frame, text="Порт:").pack(anchor=tk.W, pady=2)
        self.port_entry = ttk.Entry(main_frame, width=10)
        self.port_entry.insert(0, "80")
        self.port_entry.pack()
        
        ttk.Label(main_frame, text="Флаги TCP (например, 'S' для SYN, 'A' для ACK):").pack(anchor=tk.W, pady=2)
        self.flags_entry = ttk.Entry(main_frame, width=10)
        self.flags_entry.insert(0, "S")
        self.flags_entry.pack()
        
        ttk.Label(main_frame, text="TTL:").pack(anchor=tk.W, pady=2)
        self.ttl_entry = ttk.Entry(main_frame, width=10)
        self.ttl_entry.insert(0, "64")
        self.ttl_entry.pack()
        
        ttk.Label(main_frame, text="Размер окна:").pack(anchor=tk.W, pady=2)
        self.window_entry = ttk.Entry(main_frame, width=10)
        self.window_entry.insert(0, "65535")
        self.window_entry.pack()
        
        ttk.Label(main_frame, text="Пейлоад (строка):").pack(anchor=tk.W, pady=2)
        self.payload_entry = ttk.Entry(main_frame, width=40)
        self.payload_entry.pack()
        
        ttk.Label(main_frame, text="Количество пакетов:").pack(anchor=tk.W, pady=2)
        self.count_entry = ttk.Entry(main_frame, width=10)
        self.count_entry.insert(0, "100")
        self.count_entry.pack()
        
        self.send_btn = ttk.Button(main_frame, text="Отправить пакеты", command=self.start_send)
        self.send_btn.pack(pady=10)
        
        self.status = ttk.Label(main_frame, text="")
        self.status.pack()

    def start_send(self):
        target = self.target_entry.get()
        port = int(self.port_entry.get())
        flags = self.flags_entry.get()
        ttl = int(self.ttl_entry.get())
        window = int(self.window_entry.get())
        payload = self.payload_entry.get().encode()
        count = int(self.count_entry.get())
        
        threading.Thread(target=self._send_packets, args=(target, port, flags, ttl, window, payload, count)).start()
        self.status.config(text="Отправка...")

    def _send_packets(self, target, port, flags, ttl, window, payload, count):
        try:
            pkt = IP(dst=target, ttl=ttl)/TCP(dport=port, flags=flags, window=window)/Raw(load=payload)
            for _ in range(count):
                send(pkt, verbose=False)
            log(f"[PacketKitchen] Отправлено {count} пакетов на {target}:{port}")
            self.after(0, lambda: self.status.config(text="Готово"))
        except Exception as e:
            log(f"[PacketKitchen] Ошибка: {e}")
            self.after(0, lambda: self.status.config(text=f"Ошибка: {e}"))
