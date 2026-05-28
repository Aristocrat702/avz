import tkinter as tk
from tkinter import ttk
from gui.tabs.attack_tab import AttackTab
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
from gui.tabs.bot_list_tab import BotListTab
from gui.tabs.bot_scan_tab import BotScanTab
from gui.tabs.bot_auto_tab import BotAutoTab
from gui.themes import THEMES
from gui.styles import apply_theme
from utils.logger import Logger
from utils.toast import ToastManager
import json, os, glob
from datetime import datetime

try:
    from PIL import ImageGrab
except ImportError:
    import pyscreenshot as ImageGrab

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AVZ-Aristo v70.0 // STRUCTURED ONSLAUGHT")
        self.root.minsize(1200, 800)
        self.root.geometry("1360x850")
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
        
        self.tab_groups = {}
        self.all_tabs = {}
        
        self._create_grouped_notebook()
        
        root.bind('<F5>', self._on_f5)
        root.bind('<F6>', self._on_f6)
        root.bind('<Control-q>', lambda e: root.destroy())
        
        self.toast.show("AVZ-Aristo v70.0 запущен", duration=2000)
        
        self.cleanup_screenshots(50)
        self.root.after(2000, self.take_all_screenshots)

    def _create_grouped_notebook(self):
        groups = {
            "⚔️ Бой": [
                ("Шторм", AttackTab),
                ("Конструктор пакетов", PacketTab),
                ("Конструктор атак", ConstructorTab),
            ],
            "🧟 Легион": [
                ("Список ботов", BotListTab),
                ("Сканирование", BotScanTab),
                ("Автозахват", BotAutoTab),
            ],
            "🛠️ Инструменты": [
                ("Разведка", ReconTab),
                ("Веб-взлом", WebTab),
                ("Эксфильтрация", ExfilTab),
                ("AI-Анализ", AITab),
                ("AI-Инженер", AIEngineerTab),
                ("Прокси", ProxyTab),
                ("Telegram", TelegramTab),
                ("Планировщик", AutoTab),
                ("Монитор", MonitorTab),
                ("Статистика", StatsTab),
                ("Диагностика", DiagnosticTab),
                ("SSH", SSHTab),
            ],
            "⚙️ Система": [
                ("Настройки", SettingsTab),
                ("Справка", HelpTab),
            ],
        }
        
        for group_name, tabs in groups.items():
            group_frame = ttk.Frame(self.notebook)
            group_nb = ttk.Notebook(group_frame)
            group_nb.pack(fill=tk.BOTH, expand=True)
            
            for tab_name, TabClass in tabs:
                tab = TabClass(group_nb)
                group_nb.add(tab, text=tab_name)
                self.all_tabs[tab] = (group_name, tab_name)
            
            self.tab_groups[group_name] = group_nb
            self.notebook.add(group_frame, text=group_name)

    def _on_f5(self):
        for group_nb in self.tab_groups.values():
            for tab_id in group_nb.tabs():
                tab = group_nb.nametowidget(tab_id)
                if isinstance(tab, AttackTab):
                    tab.start()
                    return

    def _on_f6(self):
        for group_nb in self.tab_groups.values():
            for tab_id in group_nb.tabs():
                tab = group_nb.nametowidget(tab_id)
                if isinstance(tab, AttackTab):
                    tab.stop()
                    return

    def cleanup_screenshots(self, max_screenshots=50):
        screenshot_dir = "screenshots"
        if not os.path.exists(screenshot_dir):
            return
        files = glob.glob(os.path.join(screenshot_dir, "screen_*.png"))
        if len(files) <= max_screenshots:
            return
        files.sort(key=os.path.getmtime)
        to_delete = files[:-max_screenshots]
        for f in to_delete:
            try:
                os.remove(f)
                self.logger.info(f"Удалён старый скриншот: {f}")
            except Exception as e:
                self.logger.error(f"Не удалось удалить {f}: {e}")
        self.logger.info(f"Очистка скриншотов: удалено {len(to_delete)}, оставлено {min(len(files), max_screenshots)}")

    def take_all_screenshots(self):
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for group_name, group_nb in self.tab_groups.items():
            for tab_id in group_nb.tabs():
                group_nb.select(tab_id)
                self.root.update()
                x = self.root.winfo_rootx()
                y = self.root.winfo_rooty()
                w = self.root.winfo_width()
                h = self.root.winfo_height()
                try:
                    img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                    filename = os.path.join(screenshots_dir, f"screen_{group_name}_{tab_id}_{date_str}.png")
                    img.save(filename)
                    self.logger.info(f"Скриншот сохранён: {filename}")
                except Exception as e:
                    self.logger.error(f"Ошибка скриншота: {e}")
        self.cleanup_screenshots(50)
