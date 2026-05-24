from tkinter import ttk
import tkinter as tk

def enable_clipboard_copy(widget, get_text_func=None):
    """Добавляет возможность копирования текста через Ctrl+C и контекстное меню."""
    def copy_to_clipboard(event=None):
        text = get_text_func() if get_text_func else ""
        if text:
            widget.clipboard_clear()
            widget.clipboard_append(text)
    widget.bind('<Control-c>', copy_to_clipboard)
    widget.bind('<Control-C>', copy_to_clipboard)
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Копировать", command=copy_to_clipboard)
    def show_menu(event):
        menu.post(event.x_root, event.y_root)
    widget.bind('<Button-3>', show_menu)
