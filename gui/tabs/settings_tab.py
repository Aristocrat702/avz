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
        
        theme_frame = ttk.Frame(nb)
        nb.add(theme_frame, text="Оформление")
        ttk.Label(theme_frame, text="Тема:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.theme_var = tk.StringVar()
        theme_cb = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly")
        theme_cb.grid(row=0, column=1, padx=5)
        ttk.Button(theme_frame, text="Применить", command=self.apply_theme).grid(row=1, column=0, columnspan=2, pady=10)
        
        update_frame = ttk.Frame(nb)
        nb.add(update_frame, text="Обновление")
        ttk.Button(update_frame, text="Проверить обновления", command=self.check_update).pack(pady=10)
        
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
        app = self.winfo_toplevel().app
        app.current_theme = THEMES[theme_name]
        apply_theme(app.root, THEMES[theme_name])
        messagebox.showinfo("Тема", f"Тема '{theme_name}' применена. Рекомендуется перезапуск.")

    def check_update(self):
        import threading
        threading.Thread(target=self._update_thread).start()

    def _update_thread(self):
        from deploy.auto_update import apply_update
        if apply_update():
            messagebox.showinfo("Обновление", "Программа обновлена! Перезапустите.")
        else:
            messagebox.showinfo("Обновление", "Нет новых версий или произошла ошибка.")
