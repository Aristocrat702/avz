import tkinter as tk
from tkinter import ttk
from gui.tabs.attack_tab import AttackTab
from gui.tabs.botnet_tab import BotnetTab
from gui.tabs.ssh_tab import SSHTab
from gui.tabs.recon_tab import ReconTab
from gui.tabs.monitor_tab import MonitorTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.help_tab import HelpTab
from gui.tabs.exfil_tab import ExfilTab
from gui.tabs.proxy_tab import ProxyTab
from gui.tabs.telegram_tab import TelegramTab
from gui.tabs.auto_tab import AutoTab
from gui.tabs.ai_tab import AITab
from gui.tabs.stats_tab import StatsTab
from gui.tabs.web_tab import WebTab
from gui.tabs.diagnostic_tab import DiagnosticTab
from gui.tabs.constructor_tab import ConstructorTab
from gui.tabs.packet_tab import PacketTab
from gui.tabs.ai_engineer_tab import AIEngineerTab
from gui.themes import THEMES
from gui.styles import apply_theme
from utils.logger import Logger
from utils.toast import ToastManager
import json, os, time
from datetime import datetime

try:
    from PIL import ImageGrab
except ImportError:
    import pyscreenshot as ImageGrab

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AVZ-Aristo v57.1 // AUTODEPLOY")
        self.root.minsize(1100, 700)
        self.root.geometry("1280x800")
        self.logger = Logger(__name__)
        self.toast = ToastManager(root)
        
        root.app = self
        
        self.settings = {}
        try:
            with open("avz_settings.json","r") as f:
                self.settings = json.load(f)
        except:
            pass
        theme_name = self.settings.get("theme", "midnight")
        self.current_theme = THEMES.get(theme_name, THEMES["midnight"])
        apply_theme(root, self.current_theme)
        
        header = tk.Frame(root, bg=self.current_theme['accent'], height=40)
        header.pack(fill=tk.X, side=tk.TOP)
        header_label = tk.Label(header, text="AVZ-ARISTO", font=('Segoe UI', 14, 'bold'),
                                bg=self.current_theme['accent'], fg='white')
        header_label.pack(pady=4)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Словарь для хранения вкладок
        self.tabs = {}
        self._create_notebook()
        
        # Горячие клавиши
        root.bind('<F5>', lambda e: self._on_f5())
        root.bind('<F6>', lambda e: self._on_f6())
        root.bind('<Control-q>', lambda e: root.destroy())
        
        self.toast.show("AVZ-Aristo v57.1 запущен", duration=2000)
        
        # Автоснятие скриншотов через 2 секунды после запуска
        self.root.after(2000, self.take_all_screenshots)

    def _create_notebook(self):
        tab_definitions = [
            ("Атаки", AttackTab),
            ("Конструктор пакетов", PacketTab),
            ("Ботнет", BotnetTab),
            ("Разведка", ReconTab),
            ("Монитор", MonitorTab),
            ("Веб-взлом", WebTab),
            ("Эксфильтрация", ExfilTab),
            ("AI-Анализ", AITab),
            ("AI-Инженер", AIEngineerTab),
            ("Конструктор атак", ConstructorTab),
            ("Планировщик", AutoTab),
            ("Прокси", ProxyTab),
            ("Telegram", TelegramTab),
            ("Статистика", StatsTab),
            ("Диагностика", DiagnosticTab),
            ("SSH", SSHTab),
            ("Настройки", SettingsTab),
            ("Справка", HelpTab),
        ]
        for name, TabClass in tab_definitions:
            try:
                tab = TabClass(self.notebook)
                self.notebook.add(tab, text=name)
                self.tabs[name] = tab
            except Exception as e:
                self.logger.error(f"Ошибка загрузки вкладки {name}: {e}")

    def _on_f5(self):
        for tab in self.tabs.values():
            if isinstance(tab, AttackTab):
                tab.start()
                break

    def _on_f6(self):
        for tab in self.tabs.values():
            if isinstance(tab, AttackTab):
                tab.stop()
                break

    def take_all_screenshots(self):
        """Делает скриншот каждой вкладки и сохраняет в screenshots/"""
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Сохраняем текущую вкладку
        current_tab = self.notebook.select()
        current_index = self.notebook.index(current_tab) if current_tab else 0
        
        for i, (name, tab) in enumerate(self.tabs.items()):
            # Переключаемся на вкладку
            self.notebook.select(i)
            self.root.update()
            # Даём время на отрисовку
            self.root.after(100)
            self.root.update()
            
            # Захватываем скриншот всего окна
            x = self.root.winfo_rootx()
            y = self.root.winfo_rooty()
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            
            try:
                img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                filename = os.path.join(screenshots_dir, f"screen_{name}_{date_str}.png")
                img.save(filename)
                self.logger.info(f"Скриншот сохранён: {filename}")
            except Exception as e:
                self.logger.error(f"Ошибка скриншота {name}: {e}")
        
        # Возвращаем исходную вкладку
        self.notebook.select(current_index)
        self.toast.show("Скриншоты всех вкладок сохранены", duration=3000)
