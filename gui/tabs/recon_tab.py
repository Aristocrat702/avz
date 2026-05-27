import tkinter as tk
from tkinter import ttk, scrolledtext
import whois, dns.resolver, requests, socket, json
from recon.scanner import get_ssl_cert

class ReconTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
    def build_ui(self):
        ttk.Label(self, text="Цель:").pack(anchor=tk.W, padx=5)
        self.target_entry = ttk.Entry(self, width=40)
        self.target_entry.pack(padx=5, pady=5)
        btn_frame = ttk.Frame(self)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Сканировать", command=self.scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Shodan", command=self.shodan_lookup).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Subdomains", command=self.subdomain_enum).pack(side=tk.LEFT, padx=5)
        self.output = scrolledtext.ScrolledText(self, width=90, height=25)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def scan(self):
        target = self.target_entry.get()
        self.output.delete(1.0,tk.END)
        # Whois, DNS, HTTP, ports, SSL... (расширенный код)
        try:
            w = whois.whois(target)
            self.output.insert(tk.END, f"WHOIS:\n{w}\n\n")
        except Exception as e:
            self.output.insert(tk.END, f"WHOIS error: {e}\n")
        try:
            for qtype in ['A','MX','NS','TXT']:
                answers = dns.resolver.resolve(target, qtype)
                self.output.insert(tk.END, f"DNS {qtype}: {', '.join(map(str, answers))}\n")
        except Exception as e:
            self.output.insert(tk.END, f"DNS error: {e}\n")
        try:
            resp = requests.head(f"http://{target}", timeout=5)
            self.output.insert(tk.END, f"HTTP Headers:\n{resp.headers}\n\n")
        except Exception as e:
            self.output.insert(tk.END, f"HTTP error: {e}\n")
        try:
            open_ports = []
            for port in [21,22,80,443,8080,3306]:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex((target, port)) == 0:
                    open_ports.append(port)
                sock.close()
            self.output.insert(tk.END, f"Open ports: {open_ports}\n")
        except: pass
    def shodan_lookup(self):
        api_key = tk.simpledialog.askstring("Shodan", "API ключ:")
        if api_key:
            import shodan
            api = shodan.Shodan(api_key)
            try:
                results = api.search(self.target_entry.get())
                self.output.insert(tk.END, f"Shodan hits: {results['total']}\n")
            except Exception as e:
                self.output.insert(tk.END, f"Shodan error: {e}\n")
    def subdomain_enum(self):
        # Простая реализация через crt.sh
        pass
