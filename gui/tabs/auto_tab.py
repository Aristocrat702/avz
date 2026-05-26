import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, json, os
from gui.widgets import RightClickMenu

class AutoTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self.running = False
        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Автоматизация (планировщик атак)", font=("Arial", 12, "bold")).pack(anchor='w')

        ttk.Label(main, text="Цель:").pack(anchor='w')
        self.target_entry = ttk.Entry(main, width=40)
        self.target_entry.pack(fill=tk.X, pady=2)
        RightClickMenu(self.target_entry)

        f = ttk.Frame(main)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="Интервал (сек):").pack(side=tk.LEFT)
        self.interval = ttk.Entry(f, width=10)
        self.interval.insert(0, "60")
        self.interval.pack(side=tk.LEFT, padx=5)

        ttk.Label(f, text="Время старта (HH:MM):").pack(side=tk.LEFT, padx=(10,0))
        self.start_time = ttk.Entry(f, width=10)
        self.start_time.insert(0, "00:00")
        self.start_time.pack(side=tk.LEFT, padx=5)

        ttk.Button(f, text="Запустить", command=self.start_scheduler).pack(side=tk.LEFT, padx=5)
        ttk.Button(f, text="Стоп", command=self.stop_scheduler).pack(side=tk.LEFT)

        self.status_label = ttk.Label(main, text="Остановлен")
        self.status_label.pack(anchor='w', pady=5)

    def start_scheduler(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Ошибка", "Введите цель")
            return
        try:
            interval = int(self.interval.get())
        except:
            interval = 60
        start_time_str = self.start_time.get().strip()
        self.running = True
        self.status_label.config(text=f"Запущен, старт в {start_time_str}, интервал {interval}с")
        threading.Thread(target=self._loop, args=(target, interval, start_time_str), daemon=True).start()

    def stop_scheduler(self):
        self.running = False
        self.status_label.config(text="Остановлен")

    def _loop(self, target, interval, start_time_str):
        # Ждём до времени старта (если задано)
        if start_time_str != "00:00":
            try:
                target_h, target_m = map(int, start_time_str.split(':'))
                while self.running:
                    now = time.localtime()
                    if now.tm_hour == target_h and now.tm_min == target_m:
                        break
                    time.sleep(30)
            except:
                pass
        # Запускаем атаку с интервалом
        while self.running:
            self.app.logger.info(f"[Планировщик] Атака {target}")
            # Здесь можно вызвать атаку через движок, пока просто лог
            time.sleep(interval)
