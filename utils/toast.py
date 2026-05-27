import tkinter as tk
import threading
import time

class ToastManager:
    def __init__(self, root):
        self.root = root
        self.active = []

    def show(self, message, duration=3000, bg='#0077ff', fg='white'):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        label = tk.Label(toast, text=message, bg=bg, fg=fg, padx=20, pady=10, font=('Segoe UI', 9, 'bold'))
        label.pack()
        x = self.root.winfo_x() + self.root.winfo_width() - 350
        y = self.root.winfo_y() + 50 + len(self.active)*60
        toast.geometry(f'+{x}+{y}')
        self.active.append(toast)
        self.root.after(duration, lambda: self._dismiss(toast))

    def _dismiss(self, toast):
        if toast in self.active:
            self.active.remove(toast)
        toast.destroy()
