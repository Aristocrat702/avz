import tkinter as tk
from tkinter import ttk, messagebox
import json
from gui.themes import THEMES
from gui.styles import apply_theme

class SettingsTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)
        
        # Основные настройки
        main_frame = ttk.Frame(nb)
        nb.add(main_frame, text="Основные")
        
        ttk.Label(main_frame, text="C2 Host:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.c2_host = ttk.Entry(main_frame, width=30)
        self.c2_host.grid(row=0, column=1, padx=5)
        ttk.Label(main_frame, text="C2 Port:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.c2_port = ttk.Entry(main_frame, width=10)
        self.c2_port.grid(row=1, column=1, padx=5, sticky=tk.W)
        ttk.Label(main_frame, text="Telegram Token:").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.tg_token = ttk.Entry(main_frame, width=50)
        self.tg_token.grid(row=2, column=1, padx=5)
        ttk.Button(main_frame, text="Сохранить", command=self.save_main).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Тема
        theme_frame = ttk.Frame(nb)
        nb.add(theme_frame, text="Оформление")
        ttk.Label(theme_frame, text="Тема:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.theme_var = tk.StringVar()
        theme_cb = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly")
        theme_cb.grid(row=0, column=1, padx=5)
        ttk.Button(theme_frame, text="Применить", command=self.apply_theme).grid(row=1, column=0, columnspan=2, pady=10)
        
        self.load_settings()

    def load_settings(self):
        try:
            with open("avz_settings.json", "r") as f:
                s = json.load(f)
            self.c2_host.insert(0, s.get("c2_host", ""))
            self.c2_port.insert(0, str(s.get("c2_port", "")))
            self.tg_token.insert(0, s.get("telegram_token", ""))
            self.theme_var.set(s.get("theme", "cyber_light"))
        except:
            pass

    def save_main(self):
        try:
            with open("avz_settings.json", "r") as f:
                s = json.load(f)
        except:
            s = {}
        s["c2_host"] = self.c2_host.get()
        s["c2_port"] = int(self.c2_port.get())
        s["telegram_token"] = self.tg_token.get()
        with open("avz_settings.json", "w") as f:
            json.dump(s, f, indent=2)
        messagebox.showinfo("Настройки", "Сохранено")

    def apply_theme(self):
        theme_name = self.theme_var.get()
        try:
            with open("avz_settings.json", "r") as f:
                s = json.load(f)
        except:
            s = {}
        s["theme"] = theme_name
        with open("avz_settings.json", "w") as f:
            json.dump(s, f, indent=2)
        # Обновляем тему в приложении
        self.master.master.master.current_theme = THEMES[theme_name]
        apply_theme(self.master.master.master.root, THEMES[theme_name])
        messagebox.showinfo("Тема", f"Тема '{theme_name}' применена. Перезапустите для полного обновления.")
