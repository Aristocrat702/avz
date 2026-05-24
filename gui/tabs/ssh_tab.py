import tkinter as tk
from tkinter import ttk, messagebox

class SSHTab(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self.create_widgets()

    def create_widgets(self):
        lbl = ttk.Label(self, text="Управление SSH-серверами", font=("Arial", 12))
        lbl.pack(pady=20)
        # Здесь можно добавить интерфейс для добавления/удаления своих серверов
        # Пока заглушка, чтобы программа не падала
        ttk.Label(self, text="Функционал в разработке").pack()