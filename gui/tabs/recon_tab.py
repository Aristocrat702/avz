import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading, socket, ssl, json, requests, whois, dns.resolver, urllib.parse
from datetime import datetime

class ReconTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self.frame)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Верхняя панель ввода
        top = ttk.Frame(main)
        top.pack(fill=tk.X, pady=5)
        ttk.Label(top, text="Цель (домен/IP):").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(top, width=40)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Сканировать", command=self.start_scan).pack(side=tk.LEFT, padx=2)

        # Результаты
        self.output = scrolledtext.ScrolledText(main, bg='white', fg='black', font=('Consolas', 9))
        self.output.pack(fill=tk.BOTH, expand=True, pady=5)

        # Панель инструментов
        tools = ttk.Frame(main)
        tools.pack(fill=tk.X, pady=5)
        ttk.Button(tools, text="Whois", command=lambda: self.run_thread(self.whois_lookup)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools, text="DNS", command=lambda: self.run_thread(self.dns_lookup)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools, text="Порты (топ 100)", command=lambda: self.run_thread(self.port_scan)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools, text="SSL", command=lambda: self.run_thread(self.ssl_info)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools, text="HTTP-заголовки", command=lambda: self.run_thread(self.http_headers)).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools, text="Очистить", command=lambda: self.output.delete(1.0, tk.END)).pack(side=tk.RIGHT, padx=2)

    def run_thread(self, func):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Ошибка", "Введите цель")
            return
        self.output.insert(tk.END, f"[*] Запуск {func.__name__} для {target}\n")
        threading.Thread(target=func, args=(target,), daemon=True).start()

    def whois_lookup(self, target):
        try:
            w = whois.whois(target)
            self.output.insert(tk.END, json.dumps(w, indent=2, default=str) + "\n")
        except Exception as e:
            self.output.insert(tk.END, f"[!] Ошибка Whois: {e}\n")

    def dns_lookup(self, target):
        try:
            for rtype in ['A', 'MX', 'NS', 'TXT']:
                try:
                    answers = dns.resolver.resolve(target, rtype)
                    for a in answers:
                        self.output.insert(tk.END, f"[{rtype}] {a}\n")
                except:
                    pass
        except Exception as e:
            self.output.insert(tk.END, f"[!] Ошибка DNS: {e}\n")

    def port_scan(self, target):
        common_ports = [21,22,23,25,53,80,110,143,443,993,995,3306,3389,5432,6379,8080,8443,9090]
        ip = target
        try:
            ip = socket.gethostbyname(target)
        except:
            pass
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    self.output.insert(tk.END, f"[+] Порт {port} открыт\n")
                sock.close()
            except:
                pass

    def ssl_info(self, target):
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((target, 443), timeout=3) as sock:
                with ctx.wrap_socket(sock, server_hostname=target) as ssock:
                    cert = ssock.getpeercert()
                    self.output.insert(tk.END, json.dumps(cert, indent=2, default=str) + "\n")
        except Exception as e:
            self.output.insert(tk.END, f"[!] Ошибка SSL: {e}\n")

    def http_headers(self, target):
        try:
            url = target if target.startswith('http') else f'http://{target}'
            r = requests.get(url, timeout=3)
            for k, v in r.headers.items():
                self.output.insert(tk.END, f"{k}: {v}\n")
        except Exception as e:
            self.output.insert(tk.END, f"[!] Ошибка HTTP: {e}\n")

    def start_scan(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Ошибка", "Введите цель")
            return
        self.output.insert(tk.END, f"[*] Полное сканирование {target}\n")
        self.run_thread(self.whois_lookup)
        self.run_thread(self.dns_lookup)
        self.run_thread(self.port_scan)
        self.run_thread(self.ssl_info)
        self.run_thread(self.http_headers)
