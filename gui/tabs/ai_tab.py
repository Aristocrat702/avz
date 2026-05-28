import tkinter as tk
from tkinter import ttk, scrolledtext
from engine.analyzer import TargetAnalyzer
from services.cloudflare_bypass import bypass_cloudflare
import threading

class AITab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="Нейро-анализ цели", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=5)
        ttk.Label(frame, text="Цель:").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(frame, width=30)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        
        analyze_btn = ttk.Button(frame, text="Анализировать", command=self.analyze)
        analyze_btn.pack(side=tk.LEFT, padx=5)
        bypass_btn = ttk.Button(frame, text="Обход WAF", command=self.bypass_waf)
        bypass_btn.pack(side=tk.LEFT, padx=5)
        
        self.output = scrolledtext.ScrolledText(self, width=80, height=15)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def analyze(self):
        target = self.target_entry.get()
        if not target:
            return
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, f"Анализ {target}...\n")
        threading.Thread(target=self._run_analysis, args=(target,)).start()

    def _run_analysis(self, target):
        analyzer = TargetAnalyzer(target)
        method, reason = analyzer.recommend()
        self.output.insert(tk.END, f"Рекомендуемый метод: {method}\nПричина: {reason}\n")
        self.output.insert(tk.END, f"Открытые порты: {analyzer.open_ports}\n")
        if analyzer.http_headers:
            self.output.insert(tk.END, f"HTTP заголовки: {analyzer.http_headers}\n")

    def bypass_waf(self):
        target = self.target_entry.get()
        if not target:
            return
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, f"Проверка обхода WAF для {target}...\n")
        threading.Thread(target=self._run_bypass, args=(target,)).start()

    def _run_bypass(self, target):
        result = bypass_cloudflare(f"http://{target}")
        if result:
            self.output.insert(tk.END, "WAF обойдён успешно!\n")
        else:
            self.output.insert(tk.END, "Не удалось обойти WAF.\n")
