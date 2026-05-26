import tkinter as tk
from tkinter import ttk, messagebox
import threading, requests
from gui.widgets import RightClickMenu

class ProxyTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._create_widgets()
        self.refresh_proxies()

    def _create_widgets(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Прокси-менеджер", font=("Arial", 12, "bold")).pack(anchor='w')
        ttk.Label(main, text="Строка прокси (socks5://...)").pack(anchor='w')
        self.proxy_entry = ttk.Entry(main, width=50)
        self.proxy_entry.pack(fill=tk.X, pady=2)
        self.proxy_entry.insert(0, "3kBTM0Ya1FXxA7k:9e3c9b9c-1a11-4022-ad68-111eac0e7e21@budget.spyderproxy.com:11000")
        ttk.Button(main, text="Добавить", command=self.add_proxy).pack(pady=2)
        ttk.Button(main, text="Проверить список", command=self.check_all_proxies).pack(pady=2)

        self.listbox = tk.Listbox(main, bg='white')
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        RightClickMenu(self.listbox, get_text_func=lambda: self.listbox.get(tk.ACTIVE))

    def add_proxy(self):
        proxy_str = self.proxy_entry.get().strip()
        if proxy_str:
            self.listbox.insert(tk.END, proxy_str)
            self.proxy_entry.delete(0, tk.END)

    def refresh_proxies(self):
        # Загружаем прокси из Spyderproxy (уже добавлен)
        pass

    def check_all_proxies(self):
        threading.Thread(target=self._check_proxies, daemon=True).start()

    def _check_proxies(self):
        for i in range(self.listbox.size()):
            proxy = self.listbox.get(i)
            # Простая проверка
            self.listbox.itemconfig(i, {'bg': 'light green' if self._test_proxy(proxy) else 'light coral'})

    def _test_proxy(self, proxy):
        try:
            requests.get("http://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=3)
            return True
        except:
            return False
