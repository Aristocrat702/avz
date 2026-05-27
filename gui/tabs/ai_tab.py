import tkinter as tk
from tkinter import ttk, scrolledtext
from engine.analyzer import TargetAnalyzer
from bypass_waf import WAFBypass
import threading, asyncio, json
from utils.widgets import ToolTip

class AITab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="Нейро-анализ цели").pack(pady=10)
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=5)
        ttk.Label(frame, text="Цель:").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(frame, width=30)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        analyze_btn = ttk.Button(frame, text="Анализировать", command=self.analyze)
        analyze_btn.pack(side=tk.LEFT, padx=5)
        bypass_btn = ttk.Button(frame, text="Обход CF", command=self.bypass_cf)
        bypass_btn.pack(side=tk.LEFT, padx=5)
        self.output = scrolledtext.ScrolledText(self, width=80, height=15)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def analyze(self):
        target = self.target_entry.get()
        if not target: return
        threading.Thread(target=self._run_analysis, args=(target,)).start()

    def _run_analysis(self, target):
        analyzer = TargetAnalyzer(target)
        method, reason = analyzer.recommend()
        self.output.insert(tk.END, f"Рекомендуемый метод: {method}\nПричина: {reason}\n")

    def bypass_cf(self):
        target = self.target_entry.get()
        if not target: return
        threading.Thread(target=self._cf_bypass, args=(target,)).start()

    def _cf_bypass(self, target):
        from cloudflare_bypass import bypass_cloudflare
        content = bypass_cloudflare(f"http://{target}")
        if content:
            self.output.insert(tk.END, "Cloudflare обойдён!\n")
        else:
            self.output.insert(tk.END, "Не удалось обойти Cloudflare.\n")
