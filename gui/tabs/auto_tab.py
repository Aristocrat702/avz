import tkinter as tk
from tkinter import ttk, messagebox
import json, os, threading, time

class AutoTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Автоматизация (планировщик)", font=("Arial", 12, "bold")).pack(anchor='w')

        ttk.Label(main, text="Цель:").pack(anchor='w')
        self.target_entry = ttk.Entry(main, width=40)
        self.target_entry.pack(fill=tk.X, pady=2)

        f = ttk.Frame(main)
        f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text="Интервал (сек):").pack(side=tk.LEFT)
        self.interval = ttk.Entry(f, width=10)
        self.interval.insert(0, "60")
        self.interval.pack(side=tk.LEFT, padx=5)
        ttk.Button(f, text="Запустить", command=self.start_scheduler).pack(side=tk.LEFT, padx=5)
        ttk.Button(f, text="Стоп", command=self.stop_scheduler).pack(side=tk.LEFT)

        self.running = False

    def start_scheduler(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Ошибка", "Введите цель")
            return
        try:
            interval = int(self.interval.get())
        except:
            interval = 60
        self.running = True
        threading.Thread(target=self._loop, args=(target, interval), daemon=True).start()
        messagebox.showinfo("Планировщик", f"Атаки на {target} каждые {interval} сек")

    def stop_scheduler(self):
        self.running = False

    def _loop(self, target, interval):
        while self.running:
            # Здесь вызов атаки через движок
            self.app.logger.info(f"[Планировщик] Атака {target}")
            time.sleep(interval)
