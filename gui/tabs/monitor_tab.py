import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random

class MonitorTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.fig = Figure(figsize=(8,4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.update_graph()

    def update_graph(self):
        self.ax.clear()
        # Пример: случайные данные
        data = [random.randint(0,100) for _ in range(10)]
        self.ax.plot(data)
        self.ax.set_title("Трафик атаки (Мбит/с)")
        self.canvas.draw()
        self.after(3000, self.update_graph)
