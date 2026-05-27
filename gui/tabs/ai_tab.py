import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog
from engine.analyzer import TargetAnalyzer
from bypass_waf import WAFBypass
import threading, asyncio
from utils.widgets import ToolTip
from croniter import croniter
from datetime import datetime

class AITab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="Нейро-анализ цели", font=("Segoe UI", 12, "bold")).pack(pady=10)

        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=5)
        ttk.Label(frame, text="Цель:").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(frame, width=30)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        ToolTip(self.target_entry, "Домен или IP")

        analyze_btn = ttk.Button(frame, text="Анализировать", command=self.analyze)
        analyze_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(analyze_btn, "Сканирование и рекомендации")

        bypass_btn = ttk.Button(frame, text="Обход WAF", command=self.bypass_waf)
        bypass_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(bypass_btn, "Попробовать обойти Web Application Firewall")

        # Автопилот
        auto_frame = ttk.LabelFrame(self, text="Автопилот")
        auto_frame.pack(fill=tk.X, padx=5, pady=10)
        ttk.Label(auto_frame, text="Cron-расписание:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.cron_entry = ttk.Entry(auto_frame, width=20)
        self.cron_entry.grid(row=0, column=1, padx=5)
        self.cron_entry.insert(0, "0 * * * *")  # каждый час
        ToolTip(self.cron_entry, "Например: */10 * * * * для каждых 10 минут")
        self.auto_method_var = tk.StringVar(value="syn")
        ttk.Label(auto_frame, text="Метод:").grid(row=1, column=0, padx=5, sticky=tk.W)
        ttk.Combobox(auto_frame, textvariable=self.auto_method_var,
                     values=["syn","udp","http","multivector"], state="readonly").grid(row=1, column=1, padx=5)
        auto_start_btn = ttk.Button(auto_frame, text="Запустить автоатаку", command=self.start_auto)
        auto_start_btn.grid(row=2, column=0, columnspan=2, pady=10)
        ToolTip(auto_start_btn, "Поставить атаку на таймер по cron")
        self.auto_status = ttk.Label(auto_frame, text="")
        self.auto_status.grid(row=3, columnspan=2)

        self.output = scrolledtext.ScrolledText(self, width=80, height=15)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def analyze(self):
        target = self.target_entry.get()
        if not target:
            return
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, f"Анализ {target}...\n")
        threading.Thread(target=self._run_analysis, args=(target,)).start()

    def _run_analysis(self, target):
        analyzer = TargetAnalyzer(target)
        method, reason = analyzer.recommend()
        self.output.insert(tk.END, f"Рекомендуемый метод: {method}\nПричина: {reason}\n")
        self.output.insert(tk.END, f"Открытые порты: {analyzer.open_ports}\n")
        if analyzer.http_headers:
            self.output.insert(tk.END, f"HTTP заголовки: {analyzer.http_headers}\n")
        self.auto_method_var.set(method)

    def bypass_waf(self):
        target = self.target_entry.get()
        if not target:
            return
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, f"Проверка обхода WAF для {target}...\n")
        threading.Thread(target=self._run_bypass, args=(target,)).start()

    def _run_bypass(self, target):
        bypass = WAFBypass()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bypass.try_bypass(f"http://{target}"))
        if result:
            self.output.insert(tk.END, "WAF обойдён успешно!\n")
        else:
            self.output.insert(tk.END, "Не удалось обойти WAF.\n")

    def start_auto(self):
        target = self.target_entry.get()
        method = self.auto_method_var.get()
        cron = self.cron_entry.get()
        if not target:
            messagebox.showwarning("Ошибка", "Введите цель")
            return
        # Добавляем в планировщик
        from engine.scheduler import Scheduler
        sched = Scheduler()
        sched.add_task(cron, method, target, 80, 60)  # предполагаем порт 80 и длительность 60
        self.auto_status.config(text=f"Автоатака {method} на {target} по расписанию {cron}")
