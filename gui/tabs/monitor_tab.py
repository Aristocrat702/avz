import tkinter as tk
from tkinter import ttk, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from engine.attack import stats
import asyncio, threading, time, queue, warnings
warnings.filterwarnings('ignore')

class MonitorTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.fig = Figure(figsize=(10,4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Цель", "Метод", "Осталось (с)")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=6)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.X, padx=5, pady=5)

        # Лента событий
        self.event_log = scrolledtext.ScrolledText(self, height=8, state=tk.NORMAL)
        self.event_log.pack(fill=tk.X, padx=5, pady=5)

        self.mbps_data = []
        self.times = []
        self.queue = queue.Queue()
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        self.process_queue()

    def process_queue(self):
        try:
            while True:
                mbps, active = self.queue.get_nowait()
                self.update_gui(mbps, active)
        except queue.Empty:
            pass
        if self.running:
            self.after(100, self.process_queue)

    def update_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.running:
            mbps, active = loop.run_until_complete(stats.get_stats())
            self.mbps_data.append(mbps)
            self.times.append(len(self.times))
            if len(self.mbps_data) > 60:
                self.mbps_data.pop(0)
                self.times.pop(0)
            self.queue.put((mbps, active))
            # Добавляем события из лога атак (последние)
            tasks = stats.get_tasks()
            for task in tasks[-5:]:
                self.queue.put((f"[Attack] {task['method']} -> {task['target']}", None))
            time.sleep(1)

    def update_gui(self, data, active):
        if active is not None:
            self.ax.clear()
            if self.mbps_data:
                self.ax.plot(self.times, self.mbps_data, color='#0077ff')
                self.ax.set_title(f"Скорость атаки (Mbps) | Активных: {active}")
                self.ax.set_xlabel("Время (с)")
                self.ax.set_ylabel("Mbps")
                self.fig.tight_layout()
                self.canvas.draw()

            for row in self.tree.get_children():
                self.tree.delete(row)
            tasks = stats.get_tasks()
            now = time.time()
            for task in tasks:
                remaining = max(0, task['end'] - now)
                self.tree.insert("", tk.END, values=(
                    task.get('id', '?'),
                    task['target'],
                    task['method'],
                    f"{int(remaining)}с"
                ))
        else:
            # Это просто сообщение события
            self.event_log.insert(tk.END, data + "\n")
            self.event_log.see(tk.END)

    def destroy(self):
        self.running = False
        super().destroy()
