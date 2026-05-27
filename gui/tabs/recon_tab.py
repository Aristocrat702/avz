import tkinter as tk
from tkinter import scrolledtext
import socket
import whois
import dns.resolver
import requests

class ReconTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="Цель (IP/домен):").pack(anchor=tk.W, padx=5, pady=5)
        self.target_entry = tk.Entry(self, width=40)
        self.target_entry.pack(padx=5)
        self.scan_btn = tk.Button(self, text="Сканировать", command=self.scan)
        self.scan_btn.pack(pady=5)
        self.output = scrolledtext.ScrolledText(self, width=80, height=20)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def scan(self):
        target = self.target_entry.get()
        self.output.delete(1.0, tk.END)
        try:
            # Whois
            w = whois.whois(target)
            self.output.insert(tk.END, f"=== WHOIS ===\n{w}\n\n")
        except Exception as e:
            self.output.insert(tk.END, f"WHOIS ошибка: {e}\n")
        try:
            # DNS
            for qtype in ['A', 'MX', 'NS']:
                answers = dns.resolver.resolve(target, qtype)
                self.output.insert(tk.END, f"DNS {qtype}: {', '.join([str(r) for r in answers])}\n")
        except Exception as e:
            self.output.insert(tk.END, f"DNS ошибка: {e}\n")
        try:
            # HTTP заголовки
            resp = requests.head(f"http://{target}", timeout=5)
            self.output.insert(tk.END, f"\nHTTP заголовки:\n{resp.headers}\n")
        except Exception as e:
            self.output.insert(tk.END, f"HTTP ошибка: {e}\n")
