# utils/toast.py
import tkinter as tk
from tkinter import messagebox

class Toast:
    """Всплывающие уведомления в GUI."""
    def __init__(self, parent):
        self.parent = parent

    def show(self, message, duration=3000):
        """Показать информационное окно с сообщением."""
        messagebox.showinfo("AVZ", str(message))