import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading, time, random, requests
from engine.attack import AsyncAttackEngine
from gui.widgets import ToolTip, RightClickMenu
from utils.helpers import load_profiles, save_profile, delete_profile

PRESETS = {
    "Cloudflare Killer": {
        "method": "CFBUAM", "flare": "http://localhost:8191/v1", "ja3": "random",
        "storm": True, "h2": True, "adaptive": True, "elite_only": True
    },
    "DDoS-Guard Crusher": {
        "method": "BOT", "storm": True, "h2": True, "jitter": 5, "adaptive": True
    },
    "WordPress Breaker": {
        "method": "POST", "target_path": "/xmlrpc.php", "threads_mult": 2, "socks5": True
    },
    "Stealth Sniper": {
        "method": "GET", "stealth": True, "jitter": 50, "elite_only": True, "ja3": "random"
    }
}

class AttackTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.proxy_mgr = app.proxy_manager
        self.attack_active = False
        self.engine = None
        self._animating = False
        self.time_limit = 0
        self.time_start = 0
        self._build_ui()
        self.app.logger.info("Вкладка Атаки v3.1 инициализирована")
        # Горячие клавиши
        self.app.root.bind('<Control-Return>', lambda e: self._start_attack())
        self.app.root.bind('<Control-Key-Return>', lambda e: self._start_attack())

    # ... (весь код предыдущей версии AttackTab без изменений, только добавлены бинды в конце __init__)
