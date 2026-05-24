import tkinter as tk
from tkinter import ttk, messagebox
import json, os

class SettingsTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._create_widgets()
        self.load_settings()

    def _create_widgets(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Настройки", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(main, text="Telegram токен:").grid(row=1, column=0, sticky='w')
        self.tg_token = ttk.Entry(main, width=50)
        self.tg_token.grid(row=1, column=1, padx=5)

        ttk.Label(main, text="Telegram chat ID:").grid(row=2, column=0, sticky='w')
        self.tg_chat = ttk.Entry(main, width=50)
        self.tg_chat.grid(row=2, column=1, padx=5)

        ttk.Label(main, text="Spyderproxy строка:").grid(row=3, column=0, sticky='w')
        self.proxy_url = ttk.Entry(main, width=50)
        self.proxy_url.grid(row=3, column=1, padx=5)

        ttk.Label(main, text="Папка loot:").grid(row=4, column=0, sticky='w')
        self.loot_dir = ttk.Entry(main, width=50)
        self.loot_dir.grid(row=4, column=1, padx=5)

        ttk.Button(main, text="Сохранить", command=self.save_settings).grid(row=5, column=0, columnspan=2, pady=10)

    def load_settings(self):
        try:
            with open("avz_settings.json") as f:
                s = json.load(f)
            self.tg_token.insert(0, s.get("telegram_token", ""))
            self.tg_chat.insert(0, s.get("telegram_chat_id", ""))
            self.proxy_url.insert(0, s.get("proxy_url", ""))
            self.loot_dir.insert(0, s.get("loot_dir", "loot"))
        except:
            pass

    def save_settings(self):
        data = {
            "telegram_token": self.tg_token.get().strip(),
            "telegram_chat_id": self.tg_chat.get().strip(),
            "proxy_url": self.proxy_url.get().strip(),
            "loot_dir": self.loot_dir.get().strip() or "loot"
        }
        with open("avz_settings.json", "w") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Успех", "Настройки сохранены")
        self.app.settings.update(data)
