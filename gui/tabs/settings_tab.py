import tkinter as tk
from tkinter import messagebox
import json

class SettingsTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="C2 Host:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.c2_host = tk.Entry(self, width=30)
        self.c2_host.grid(row=0, column=1, padx=5)
        tk.Label(self, text="C2 Port:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.c2_port = tk.Entry(self, width=10)
        self.c2_port.grid(row=1, column=1, padx=5, sticky=tk.W)
        tk.Label(self, text="Telegram Token:").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.tg_token = tk.Entry(self, width=50)
        self.tg_token.grid(row=2, column=1, padx=5)
        tk.Button(self, text="Сохранить", command=self.save_settings).grid(row=3, column=0, columnspan=2, pady=10)
        self.load_settings()

    def load_settings(self):
        try:
            with open("avz_settings.json", "r") as f:
                s = json.load(f)
            self.c2_host.insert(0, s.get("c2_host", ""))
            self.c2_port.insert(0, str(s.get("c2_port", "")))
            self.tg_token.insert(0, s.get("telegram_token", ""))
        except:
            pass

    def save_settings(self):
        s = {
            "c2_host": self.c2_host.get(),
            "c2_port": int(self.c2_port.get()),
            "telegram_token": self.tg_token.get()
        }
        with open("avz_settings.json", "w") as f:
            json.dump(s, f)
        messagebox.showinfo("Настройки", "Сохранено")
