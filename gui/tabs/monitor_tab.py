import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading, time, random

class MonitorTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self.running = False
        self.rps_history = [0] * 60
        self._create_widgets()

    def _create_widgets(self):
        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("RPS (атак)", color="black")
        self.ax.set_facecolor("white")
        self.canvas = FigureCanvasTkAgg(self.figure, self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=5)
        self.btn_start = ttk.Button(btn_frame, text="▶ Старт", command=self.start_monitoring)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="■ Стоп", command=self.stop_monitoring).pack(side=tk.LEFT, padx=5)

        self.stats_label = ttk.Label(self.frame, text="RPS: 0")
        self.stats_label.pack()

    def start_monitoring(self):
        if not self.running:
            self.running = True
            self.btn_start.config(text="⏸ Пауза")
            threading.Thread(target=self._fetch_data_loop, daemon=True).start()
            self._animate()

    def stop_monitoring(self):
        self.running = False
        self.btn_start.config(text="▶ Старт")

    def _fetch_data_loop(self):
        while self.running:
            try:
                # Получаем RPS из движка атаки
                if hasattr(self.app, 'attack_engine') and self.app.attack_engine:
                    rps = self.app.attack_engine.stats.get('rps', 0)
                else:
                    rps = 0
                self.rps_history.append(rps)
                self.rps_history.pop(0)
                self.stats_label.config(text=f"RPS: {rps}")
            except:
                pass
            time.sleep(1)

    def _animate(self):
        if self.running:
            self._update_plot()
            self.frame.after(1000, self._animate)

    def _update_plot(self):
        self.ax.clear()
        self.ax.plot(self.rps_history, color="#3399ff")
        self.ax.set_title("RPS (атак)", color="black")
        self.ax.set_facecolor("white")
        self.canvas.draw()
