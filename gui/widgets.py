import tkinter as tk
from tkinter import ttk
from utils.clipboard import enable_clipboard_copy

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)
    def show(self, e):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")
        frame = tk.Frame(self.tip, bg="#1a1a1a", bd=1, relief=tk.SOLID)
        frame.pack()
        tk.Label(frame, text=self.text, bg="#1a1a1a", fg="#00ff41", font=('Consolas', 9), padx=6, pady=3).pack()
    def hide(self, e):
        if self.tip:
            self.tip.destroy()

class RightClickMenu:
    def __init__(self, widget, get_text_func=None, extra_commands=None):
        self.widget = widget
        if get_text_func:
            self.get_text = get_text_func
        else:
            self.get_text = self._default_get_text
        self.menu = tk.Menu(widget, tearoff=0, bg='#1a1a1a', fg='#00ff41', activebackground='#333', activeforeground='#00ff41')
        self.menu.add_command(label="📋 Копировать", command=self.copy)
        self.menu.add_command(label="📄 Вставить", command=self.paste)
        if extra_commands:
            self.menu.add_separator()
            for label, command in extra_commands:
                self.menu.add_command(label=label, command=command)
        widget.bind("<Button-3>", self.show_menu)
        enable_clipboard_copy(widget)

    def _default_get_text(self):
        try:
            if isinstance(self.widget, tk.Text):
                if self.widget.tag_ranges(tk.SEL):
                    return self.widget.selection_get()
                else:
                    return self.widget.get("1.0", tk.END).rstrip('\n')
            elif isinstance(self.widget, tk.Entry):
                if self.widget.selection_present():
                    return self.widget.selection_get()
                else:
                    return self.widget.get()
            elif isinstance(self.widget, ttk.Entry):
                return self.widget.get()
            else:
                return ""
        except:
            return ""

    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def copy(self):
        text = self.get_text()
        if text:
            self.widget.clipboard_clear()
            self.widget.clipboard_append(text)

    def paste(self):
        try:
            text = self.widget.clipboard_get()
            if isinstance(self.widget, (tk.Text,)):
                self.widget.insert(tk.INSERT, text)
            elif isinstance(self.widget, (tk.Entry, ttk.Entry)):
                self.widget.insert(tk.INSERT, text)
        except:
            pass

    def add_separator(self):
        self.menu.add_separator()

    def add_command(self, label, command):
        self.menu.add_command(label=label, command=command)
