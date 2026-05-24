import tkinter as tk
from tkinter import ttk

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from matplotlib.animation import FuncAnimation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class MonitorTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="📊 Мониторинг")
        self.data_rps = []
        self.data_total = []
        self.max_points = 60
        self.ani = None
        self._build_ui()

    def _build_ui(self):
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(8, 4), dpi=100, facecolor=self.app.bg)
            self.ax = self.figure.add_subplot(111)
            self.ax.set_facecolor(self.app.bg)
            self.ax.tick_params(colors=self.app.fg)
            self.ax.spines['bottom'].set_color(self.app.accent)
            self.ax.spines['left'].set_color(self.app.accent)
            self.ax.grid(True, linestyle='--', alpha=0.3)
            self.line_rps, = self.ax.plot([], [], color=self.app.success, linewidth=2, label='RPS')
            self.line_total, = self.ax.plot([], [], color=self.app.warning, linewidth=1, label='Всего запросов')
            self.ax.legend(loc='upper left')
            self.ax.set_xlabel('Время (сек)', color=self.app.fg)
            self.ax.set_ylabel('Запросы', color=self.app.fg)
            self.canvas = FigureCanvasTkAgg(self.figure, self.frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self._start_animation()
        else:
            # Заглушка без matplotlib
            self.text = tk.Text(self.frame, bg=self.app.colors['entry_bg'], fg=self.app.fg, height=10)
            self.text.pack(fill=tk.BOTH, expand=True)
            self.text.insert(tk.END, "Модуль matplotlib не установлен.\nУстановите его для отображения графиков.\n\nТекущие значения:\n")
            self.text.configure(state='disabled')

    def _start_animation(self):
        if MATPLOTLIB_AVAILABLE:
            self.ani = FuncAnimation(self.figure, self._update_plot, interval=1000, blit=False, cache_frame_data=False)

    def _update_plot(self, frame):
        if not self.data_rps:
            self.data_rps.append(0)
            self.data_total.append(0)
        self.line_rps.set_data(range(len(self.data_rps)), self.data_rps)
        self.line_total.set_data(range(len(self.data_total)), self.data_total)
        self.ax.relim()
        self.ax.autoscale_view(scalex=True, scaley=True)
        self._apply_gradient()
        return self.line_rps, self.line_total

    def _apply_gradient(self):
        if not self.data_rps:
            return
        self.ax.collections.clear()
        x = range(len(self.data_rps))
        y = self.data_rps
        if len(y) > 1:
            self.ax.fill_between(x, y, alpha=0.2, color=self.app.success, linewidth=0)
            self.ax.fill_between(range(len(self.data_total)), self.data_total, alpha=0.1, color=self.app.warning, linewidth=0)

    def refresh_plot(self, data):
        self.data_rps = data[0][-self.max_points:]
        self.data_total = data[1][-self.max_points:]
        if not MATPLOTLIB_AVAILABLE:
            self.text.configure(state='normal')
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, f"Текущие значения:\nRPS: {self.data_rps[-1] if self.data_rps else 0:.1f}\nВсего: {self.data_total[-1] if self.data_total else 0}")
            self.text.configure(state='disabled')