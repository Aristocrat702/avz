import tkinter as tk
import threading, time

class Toast:
    """Всплывающее окно в стиле 'тост'."""
    def __init__(self, root, message, duration=3, bg='#333333', fg='white'):
        self.root = root
        self.duration = duration
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.0)
        self.window.configure(bg=bg)
        frame = tk.Frame(self.window, bg=bg, padx=15, pady=10)
        frame.pack()
        label = tk.Label(frame, text=message, bg=bg, fg=fg, font=('Arial', 10))
        label.pack()
        # Позиция в правом нижнем углу
        self.window.update_idletasks()
        x = root.winfo_screenwidth() - self.window.winfo_width() - 30
        y = root.winfo_screenheight() - self.window.winfo_height() - 60
        self.window.geometry(f"+{x}+{y}")
        self._fade_in()

    def _fade_in(self, alpha=0.0):
        if alpha < 1.0:
            alpha += 0.1
            self.window.attributes('-alpha', alpha)
            self.window.after(30, self._fade_in, alpha)
        else:
            self.window.after(int(self.duration * 1000), self._fade_out)

    def _fade_out(self, alpha=1.0):
        if alpha > 0.0:
            alpha -= 0.1
            self.window.attributes('-alpha', alpha)
            self.window.after(30, self._fade_out, alpha)
        else:
            self.window.destroy()
