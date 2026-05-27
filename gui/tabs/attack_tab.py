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
                "Mixed Hell": {"method":"mixed","port":80,"duration":90},
                "Multivector Burst": {"method":"multivector","port":80,"duration":120},
                "TLS Exhaust": {"method":"tls_exhaustion","port":443,"duration":120}
            }
    def build_ui(self):
        methods = ["udp","tcp","syn","icmp","slowloris","http","dns_amp","ntp_amp","mixed","multivector","tls_exhaustion"]
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Простая атака
        simple_frame = ttk.LabelFrame(main_frame, text="Быстрый удар")
        simple_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(simple_frame, text="Метод:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.method_var = tk.StringVar(value="syn")
        method_cb = ttk.Combobox(simple_frame, textvariable=self.method_var, values=methods, state="readonly")
        method_cb.grid(row=0, column=1, padx=5)
        ToolTip(method_cb, "Выберите вектор атаки")
        
        ttk.Label(simple_frame, text="Пресет:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.preset_var = tk.StringVar()
        preset_cb = ttk.Combobox(simple_frame, textvariable=self.preset_var, values=[""]+list(self.presets.keys()), state="readonly")
        preset_cb.grid(row=1, column=1, padx=5)
        ToolTip(preset_cb, "Быстрая загрузка сохранённого профиля")
        self.preset_var.trace('w', self.on_preset)
        
        ttk.Label(simple_frame, text="Цель:").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.target_entry = ttk.Entry(simple_frame, width=30)
        self.target_entry.grid(row=2, column=1, padx=5)
        ToolTip(self.target_entry, "IP или домен цели")
        
        ttk.Label(simple_frame, text="Порт:").grid(row=3, column=0, padx=5, sticky=tk.W)
        self.port_entry = ttk.Entry(simple_frame, width=10)
        self.port_entry.insert(0, "80")
        self.port_entry.grid(row=3, column=1, padx=5, sticky=tk.W)
        ToolTip(self.port_entry, "Порт сервиса")
        
        ttk.Label(simple_frame, text="Длительность (с):").grid(row=4, column=0, padx=5, sticky=tk.W)
        self.duration_entry = ttk.Entry(simple_frame, width=10)
        self.duration_entry.insert(0, "60")
        self.duration_entry.grid(row=4, column=1, padx=5, sticky=tk.W)
        ToolTip(self.duration_entry, "Секунды атаки")
        
        btn_frame = ttk.Frame(simple_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        self.start_btn = ttk.Button(btn_frame, text="ЗАПУСТИТЬ", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.start_btn, "Начать штурм")
        self.stop_btn = ttk.Button(btn_frame, text="СТОП", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.stop_btn, "Прервать текущую атаку")
        
        self.status = ttk.Label(simple_frame, text="Готов", font=('Segoe UI', 9, 'italic'))
        self.status.grid(row=6, column=0, columnspan=2, pady=5)
        
        self.progress = ttk.Progressbar(simple_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=5)

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
        self.status.config(text="Атака идёт...")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        threading.Thread(target=self._run, args=(method, target, port, duration), daemon=True).start()
    def stop(self):
        self.status.config(text="Остановлено")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
    def _run(self, method, target, port, duration):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.engine.run_attack(method, target, port, duration))
        self.status.config(text="Завершено")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
