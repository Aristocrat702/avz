import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests, threading
from gui.widgets import RightClickMenu

class TelegramTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Telegram-бот (уведомления)", font=("Arial", 12, "bold")).pack(anchor='w')

        f1 = ttk.Frame(main)
        f1.pack(fill=tk.X, pady=5)
        ttk.Label(f1, text="Токен:").pack(side=tk.LEFT)
        self.token_entry = ttk.Entry(f1, width=50)
        self.token_entry.pack(side=tk.LEFT, padx=5)
        RightClickMenu(self.token_entry)

        f2 = ttk.Frame(main)
        f2.pack(fill=tk.X, pady=5)
        ttk.Label(f2, text="Chat ID:").pack(side=tk.LEFT)
        self.chat_entry = ttk.Entry(f2, width=50)
        self.chat_entry.pack(side=tk.LEFT, padx=5)
        RightClickMenu(self.chat_entry)

        ttk.Button(main, text="Проверить связь", command=self.test_connection).pack(pady=5)

        self.log = scrolledtext.ScrolledText(main, height=10, bg='white')
        self.log.pack(fill=tk.BOTH, expand=True)
        RightClickMenu(self.log)

    def test_connection(self):
        token = self.token_entry.get().strip()
        chat = self.chat_entry.get().strip()
        if not token or not chat:
            messagebox.showwarning("Ошибка", "Введите токен и chat ID")
            return
        def test():
            try:
                resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                                     json={"chat_id": chat, "text": "AVZ-тест"}, timeout=5)
                if resp.status_code == 200:
                    self.log.insert(tk.END, "[+] Связь с Telegram установлена\n")
                else:
                    self.log.insert(tk.END, f"[-] Ошибка: {resp.text}\n")
            except Exception as e:
                self.log.insert(tk.END, f"[-] Исключение: {e}\n")
        threading.Thread(target=test, daemon=True).start()
