import tkinter as tk
from tkinter import ttk
import time
from engine.attack import stats
from utils.widgets import add_copy_paste_support

class MonitorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()
        add_copy_paste_support(self)
        self.update_stats()

    def create_widgets(self):
        frame = ttk.LabelFrame(self, text="Активные атаки")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("target", "method", "duration")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("target", text="Цель")
        self.tree.heading("method", text="Метод")
        self.tree.heading("duration", text="Длительность (сек)")
        self.tree.column("target", width=200)
        self.tree.column("method", width=150)
        self.tree.column("duration", width=100)
        
        scroll = ttk.Scrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        self.active_label = ttk.Label(stats_frame, text="Активных атак: 0")
        self.active_label.pack(side=tk.LEFT, padx=10)
        self.traffic_label = ttk.Label(stats_frame, text="Трафик: 0 MB")
        self.traffic_label.pack(side=tk.LEFT, padx=10)

    def update_stats(self):
        active = stats.get_stats()["active"]
        traffic = stats.total_traffic_mb
        self.active_label.config(text=f"Активных атак: {active}")
        self.traffic_label.config(text=f"Трафик: {traffic} MB")
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        for task in stats.get_tasks():
            self.tree.insert("", tk.END, values=(task["target"], task["method"], int(time.time() - task["start"])))
        
        self.after(1000, self.update_stats)
