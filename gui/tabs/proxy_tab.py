import tkinter as tk
from tkinter import ttk, messagebox
import threading, requests
from gui.widgets import RightClickMenu

class ProxyTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Прокси-менеджер", font=("Arial", 12, "bold")).pack(anchor='w')
        ttk.Label(main, text="Источник: Spyderproxy (автообновление)").pack(anchor='w')
        ttk.Button(main, text="Обновить список сейчас", command=self.refresh_proxies).pack(pady=5)

        self.listbox = tk.Listbox(main, bg='white')
        self.listbox.pack(fill=tk.BOTH, expand=True)
        RightClickMenu(self.listbox, get_text_func=lambda: self.listbox.get(tk.ACTIVE))

    def refresh_proxies(self):
        def fetch():
            self.listbox.delete(0, tk.END)
            if hasattr(self.app, 'proxy_manager'):
                self.app.proxy_manager.update_proxies()
                proxies = self.app.proxy_manager.get_best_proxies(50)
                for p in proxies:
                    self.listbox.insert(tk.END, p)
            else:
                self.listbox.insert(tk.END, "Менеджер прокси недоступен")
        threading.Thread(target=fetch, daemon=True).start()
