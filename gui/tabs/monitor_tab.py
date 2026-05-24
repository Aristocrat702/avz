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
        # notebook.add(self.frame, text="Мониторинг")  # удалено
        self.running = False
        self.rps_history = [0] * 60
        self._create_widgets()

    def _create_widgets(self):
        # ... (весь остальной код без изменений)
        pass
