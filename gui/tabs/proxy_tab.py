import tkinter as tk
from tkinter import scrolledtext
from engine.proxy import ProxyManager

class ProxyTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pm = ProxyManager()
        self.build_ui()

    def build_ui(self):
        self.text = scrolledtext.ScrolledText(self, width=80, height=20)
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for i, p in enumerate(self.pm.proxies):
            self.text.insert(tk.END, f"Прокси {i+1}: {p}\n")
