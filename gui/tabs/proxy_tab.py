import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.widgets import ToolTip, RightClickMenu

class ProxyTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="🌐 Прокси")
        self._build_ui()
        self.manager = app.proxy_manager
        self.manager.log = self._log
        self.manager.progress = self._update_progress
        self.manager.status = self._update_status
        if not self.manager.load_cache():
            self._log("Кэш пуст или устарел. Нажмите «▶ Сбор»\n")
        else:
            self._refresh_table()

    def _build_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=0)
        self.frame.rowconfigure(2, weight=1)
        self.frame.rowconfigure(3, weight=0)

        ctrl = ttk.Frame(self.frame)
        ctrl.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        ttk.Button(ctrl, text="▶ Сбор прокси", command=self._start_gather).pack(side=tk.LEFT, padx=5)
        ToolTip(ctrl.winfo_children()[-1], "Загрузить и проверить прокси из 1000+ источников")
        ttk.Button(ctrl, text="⏹ Стоп", command=lambda: setattr(self.manager, 'stop_flag', True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="📋 HTTP", command=lambda: self._copy_to_clipboard('http')).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="📋 SOCKS5", command=lambda: self._copy_to_clipboard('socks5')).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="💾 Сохранить", command=self._save_to_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="🗺 Карта", command=self._show_map).pack(side=tk.LEFT, padx=5)
        self.proxy_progress = ttk.Progressbar(ctrl, length=150, mode='determinate')
        self.proxy_progress.pack(side=tk.RIGHT, padx=10)

        filter_frame = ttk.LabelFrame(self.frame, text="Фильтры и настройки", padding=5)
        filter_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        ttk.Label(filter_frame, text="Макс. задержка (сек):").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(filter_frame, from_=0.5, to=5.0, increment=0.1, textvariable=self.speed_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(filter_frame, text="Страна (код):").pack(side=tk.LEFT, padx=(10,0))
        self.geo_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.geo_var, width=5).pack(side=tk.LEFT, padx=5)
        self.elite_var = tk.BooleanVar()
        ttk.Checkbutton(filter_frame, text="Только элитные", variable=self.elite_var).pack(side=tk.LEFT, padx=10)
        self.fast_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Быстрый сбор", variable=self.fast_var).pack(side=tk.LEFT, padx=10)
        ttk.Label(filter_frame, text="API-ключ:").pack(side=tk.LEFT, padx=(10,0))
        self.premium_key_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.premium_key_var, width=20).pack(side=tk.LEFT, padx=5)

        columns = ('ip', 'port', 'type', 'speed', 'score', 'country', 'anonymous')
        self.tree = ttk.Treeview(self.frame, columns=columns, show='headings', height=15)
        self.tree.heading('ip', text='IP'); self.tree.column('ip', width=130)
        self.tree.heading('port', text='Порт'); self.tree.column('port', width=60)
        self.tree.heading('type', text='Тип'); self.tree.column('type', width=70)
        self.tree.heading('speed', text='Скорость'); self.tree.column('speed', width=80)
        self.tree.heading('score', text='Скор'); self.tree.column('score', width=60)
        self.tree.heading('country', text='Страна'); self.tree.column('country', width=80)
        self.tree.heading('anonymous', text='Анонимность'); self.tree.column('anonymous', width=100)
        self.tree.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.log_text = tk.Text(self.frame, height=6, bg='#1e1e1e' if self.app.theme=='dark' else 'white',
                                fg='lime' if self.app.theme=='dark' else 'black')
        self.log_text.grid(row=3, column=0, sticky='ew', padx=10, pady=5)
        RightClickMenu(self.log_text, get_text_func=lambda: self.log_text.get("1.0", tk.END).strip())

    def _start_gather(self):
        if self.manager.running:
            messagebox.showinfo("Занято", "Сбор прокси уже выполняется")
            return
        self.log_text.delete(1.0, tk.END)
        self.proxy_progress['value'] = 0  # Сброс прогресс-бара
        self.app.logger.info("Сбор прокси запущен")
        threading.Thread(target=self.manager.gather,
                         args=(self.speed_var.get(), self.geo_var.get().upper(), self.elite_var.get(), self.fast_var.get()),
                         daemon=True).start()
        self.frame.after(2000, self._auto_refresh)

    def _auto_refresh(self):
        if self.manager.running:
            self._refresh_table()
            self.frame.after(2000, self._auto_refresh)
        else:
            self._refresh_table()

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for p in self.manager.proxies:
            self.tree.insert('', tk.END, values=(p['ip'], p['port'], p['type'],
                                                 p['speed'], p.get('score', ''), p.get('country',''), p.get('anonymous','')))

    def _copy_to_clipboard(self, typ):
        proxies = [f"{p['ip']}:{p['port']}" for p in self.manager.proxies if p['type'] == typ]
        if proxies:
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append("\n".join(proxies))
            messagebox.showinfo("Скопировано", f"Скопировано {len(proxies)} {typ.upper()} прокси")
        else:
            messagebox.showwarning("Пусто", f"Нет прокси типа {typ.upper()}")

    def _save_to_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            with open(filename, 'w') as f:
                for p in self.manager.proxies:
                    f.write(f"{p['ip']}:{p['port']} {p['type']} {p['speed']}\n")
            messagebox.showinfo("Сохранено", f"Прокси сохранены в {filename}")

    def _show_map(self):
        points = self.manager.get_map_data()
        if not points:
            messagebox.showinfo("Нет данных", "Нет прокси для отображения")
            return
        map_window = tk.Toplevel(self.frame)
        map_window.title("Карта прокси")
        fig, ax = plt.subplots(figsize=(10, 6))
        lats = [p[0] for p in points]
        lons = [p[1] for p in points]
        scores = [p[2] for p in points]
        ax.scatter(lons, lats, c=scores, cmap='RdYlGn', s=30, edgecolors='black', linewidth=0.5)
        ax.set_xlabel('Долгота')
        ax.set_ylabel('Широта')
        ax.set_title('Распределение прокси (цвет — скор)')
        canvas = FigureCanvasTkAgg(fig, master=map_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _log(self, msg):
        self.log_text.insert(tk.END, msg)
        self.log_text.see(tk.END)

    def _update_progress(self, val):
        self.proxy_progress['value'] = val

    def _update_status(self, text):
        pass