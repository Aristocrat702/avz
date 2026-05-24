import tkinter as tk
from tkinter import ttk, messagebox
from utils.helpers import save_settings

class SettingsTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="⚙️ Настройки")
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        # Прокси
        proxy_frame = ttk.LabelFrame(self.frame, text="Прокси", padding=10)
        proxy_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(proxy_frame, text="Автообновление (минут, 0=выкл):").grid(row=0, column=0, sticky='w')
        self.auto_update_var = tk.IntVar()
        ttk.Spinbox(proxy_frame, from_=0, to=1440, textvariable=self.auto_update_var, width=5).grid(row=0, column=1, sticky='w')

        ttk.Label(proxy_frame, text="Макс. задержка прокси (сек):").grid(row=1, column=0, sticky='w')
        self.speed_limit_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(proxy_frame, from_=0.1, to=5.0, increment=0.1, textvariable=self.speed_limit_var, width=5).grid(row=1, column=1, sticky='w')

        ttk.Label(proxy_frame, text="Геофильтр (код страны):").grid(row=2, column=0, sticky='w')
        self.geo_var = tk.StringVar()
        ttk.Entry(proxy_frame, textvariable=self.geo_var, width=6).grid(row=2, column=1, sticky='w')

        self.elite_var = tk.BooleanVar()
        ttk.Checkbutton(proxy_frame, text="Только элитные прокси", variable=self.elite_var).grid(row=3, column=0, columnspan=2, sticky='w')

        # Telegram
        tg_frame = ttk.LabelFrame(self.frame, text="Telegram", padding=10)
        tg_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(tg_frame, text="Токен:").grid(row=0, column=0, sticky='w')
        self.tg_token_var = tk.StringVar()
        ttk.Entry(tg_frame, textvariable=self.tg_token_var, width=50).grid(row=0, column=1, padx=5)

        ttk.Label(tg_frame, text="Chat ID:").grid(row=1, column=0, sticky='w')
        self.tg_chat_var = tk.StringVar()
        ttk.Entry(tg_frame, textvariable=self.tg_chat_var, width=50).grid(row=1, column=1, padx=5)

        # Интерфейс
        ui_frame = ttk.LabelFrame(self.frame, text="Интерфейс", padding=10)
        ui_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(ui_frame, text="Тема:").grid(row=0, column=0, sticky='w')
        self.theme_var = tk.StringVar(value=self.app.theme)
        ttk.Radiobutton(ui_frame, text="Тёмная", variable=self.theme_var, value='dark').grid(row=0, column=1, sticky='w')
        ttk.Radiobutton(ui_frame, text="Светлая", variable=self.theme_var, value='light').grid(row=0, column=2, sticky='w')

        self.tray_var = tk.BooleanVar(value=self.app.settings.get('tray_enabled', True))
        ttk.Checkbutton(ui_frame, text="Сворачивать в трей", variable=self.tray_var).grid(row=1, column=0, columnspan=3, sticky='w')

        # Кнопки
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="💾 Сохранить", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Сброс", command=self._load_current).pack(side=tk.LEFT, padx=5)

    def _load_current(self):
        s = self.app.settings
        self.auto_update_var.set(s.get('auto_update_proxies', 0))
        self.speed_limit_var.set(s.get('proxy_speed_limit', 1.0))
        self.geo_var.set(s.get('geo_filter', ''))
        self.elite_var.set(s.get('elite_only', False))
        self.tg_token_var.set(s.get('telegram_token', ''))
        self.tg_chat_var.set(s.get('telegram_chat_id', ''))
        self.theme_var.set(s.get('theme', 'dark'))
        self.tray_var.set(s.get('tray_enabled', True))

    def _save(self):
        self.app.settings['auto_update_proxies'] = self.auto_update_var.get()
        self.app.settings['proxy_speed_limit'] = self.speed_limit_var.get()
        self.app.settings['geo_filter'] = self.geo_var.get().upper()
        self.app.settings['elite_only'] = self.elite_var.get()
        self.app.settings['telegram_token'] = self.tg_token_var.get()
        self.app.settings['telegram_chat_id'] = self.tg_chat_var.get()
        self.app.settings['theme'] = self.theme_var.get()
        self.app.settings['tray_enabled'] = self.tray_var.get()

        save_settings(self.app.settings)
        messagebox.showinfo("Настройки", "Сохранено. Некоторые изменения вступят в силу после перезапуска.")
        # Можно сразу применить тему (упрощённо)
        if self.theme_var.get() != self.app.theme:
            self.app.theme = self.theme_var.get()
            self.app.bg = "#1e1e1e" if self.app.theme == "dark" else "#f0f0f0"
            self.app.fg = "white" if self.app.theme == "dark" else "black"
            self.app.root.configure(bg=self.app.bg)
            self.app._apply_ttk_style()