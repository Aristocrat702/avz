import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from engine.attack import stats
import asyncio, threading, time

class MonitorTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.fig = Figure(figsize=(10,5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.mbps_data = []
        self.times = []
        self.running = True
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()
    def update_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.running:
            mbps, active = loop.run_until_complete(stats.get_stats())
            self.mbps_data.append(mbps)
            self.times.append(time.strftime('%H:%M:%S'))
            if len(self.mbps_data) > 60:
                self.mbps_data.pop(0)
                self.times.pop(0)
            self.ax.clear()
            self.ax.plot(self.times, self.mbps_data, color='red')
            self.ax.set_title(f"Live Traffic (Mbps) | Active Attacks: {active}")
            self.ax.tick_params(axis='x', rotation=45)
            self.fig.tight_layout()
            self.canvas.draw()
            time.sleep(1)
