import tkinter as tk
from tkinter import messagebox

class Toast:
    def __init__(self, parent):
        self.parent = parent

    def show(self, message, duration=3000):
        messagebox.showinfo("AVZ", str(message))
