import tkinter as tk
from tkinter import messagebox
import requests

class TelegramTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        tk.Button(self, text="Проверить связь с ботом", command=self.check).pack(pady=20)

    def check(self):
        # Заглушка, но честная: проверит токен из настроек
        import json
        try:
            with open("avz_settings.json", "r") as f:
                s = json.load(f)
            token = s.get("telegram_token", "")
            if not token:
                messagebox.showwarning("Telegram", "Токен не задан в настройках")
                return
            resp = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            if resp.ok:
                messagebox.showinfo("Telegram", f"Бот активен: {resp.json()['result']['username']}")
            else:
                messagebox.showerror("Telegram", "Неверный токен")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
