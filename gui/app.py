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
from gui.tabs.loot_tab import LootTab
from gui.tabs.proxy_tab import ProxyTab
from gui.tabs.telegram_tab import TelegramTab
from gui.tabs.auto_tab import AutoTab
from gui.tabs.diagnostic_tab import DiagnosticTab
from gui.tabs.ai_tab import AITab
from gui.tabs.stats_tab import StatsTab
from utils.logger import Logger

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AVZ-Aristo v30.0 ULTIMATE")
        self.logger = Logger(__name__)
        style = ttk.Style()
        style.theme_use('clam')
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self._create_notebook()
    def _create_notebook(self):
        tabs = [
            ("Атака", AttackTab),
            ("Ботнет", BotnetTab),
            ("SSH", SSHTab),
            ("Разведка", ReconTab),
            ("Монитор", MonitorTab),
            ("Exfil", ExfilTab),
            ("Loot", LootTab),
            ("Прокси", ProxyTab),
            ("Telegram", TelegramTab),
            ("Авто", AutoTab),
            ("AI", AITab),
            ("Статистика", StatsTab),
            ("Диагностика", DiagnosticTab),
            ("Настройки", SettingsTab),
            ("Справка", HelpTab),
        ]
        for name, TabClass in tabs:
            tab = TabClass(self.notebook)
            self.notebook.add(tab, text=name)
