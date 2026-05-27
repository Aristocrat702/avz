import tkinter as tk
from tkinter import scrolledtext
import subprocess
import os

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

    def check_vps(self):
        self.output.insert(tk.END, "Проверка VPS (ping)...\n")
        import json
        try:
            with open("avz_settings.json","r") as f:
                host = json.load(f).get("c2_host", "80.249.146.202")
        except:
            host = "80.249.146.202"
        res = subprocess.run(["ping", "-n", "2", host], capture_output=True, text=True)
        self.output.insert(tk.END, res.stdout)

    def redeploy_agent(self):
        self.output.insert(tk.END, "Команда обновления агента на VPS отправлена (заглушка).\n")
