import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StatsTab(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self.bot_history = [0] * 60
        self._create_widgets()
        self.after(5000, self._update_graph)

    def _create_widgets(self):
        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Рост ботов (последние 5 минут)", color="black")
        self.ax.set_facecolor("white")
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_graph(self):
        if hasattr(self.app, 'botnet_tab'):
            bot_count = len(self.app.botnet_tab.bots)
            self.bot_history.append(bot_count)
            self.bot_history.pop(0)
        self.ax.clear()
        self.ax.plot(self.bot_history, color="#3399ff")
        self.ax.set_title("Рост ботов", color="black")
        self.ax.set_facecolor("white")
        self.canvas.draw()
        self.after(5000, self._update_graph)
