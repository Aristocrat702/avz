import tkinter as tk
from tkinter import ttk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffff", foreground="#000000",
                         relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 8, "normal"))
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def add_copy_paste_support(widget):
    """Добавляет стандартное контекстное меню и горячие клавиши для копирования/вставки."""
    if isinstance(widget, tk.Text):
        widget.bind('<Control-c>', lambda e: widget.event_generate('<<Copy>>'))
        widget.bind('<Control-x>', lambda e: widget.event_generate('<<Cut>>'))
        widget.bind('<Control-v>', lambda e: widget.event_generate('<<Paste>>'))
    elif isinstance(widget, tk.Entry):
        widget.bind('<Control-c>', lambda e: widget.event_generate('<<Copy>>'))
        widget.bind('<Control-x>', lambda e: widget.event_generate('<<Cut>>'))
        widget.bind('<Control-v>', lambda e: widget.event_generate('<<Paste>>'))
    elif isinstance(widget, ttk.Treeview):
        def copy_tree_selection(event=None):
            selection = widget.selection()
            if selection:
                item = selection[0]
                values = widget.item(item, 'values')
                if values:
                    text = '\t'.join(str(v) for v in values)
                    widget.clipboard_clear()
                    widget.clipboard_append(text)
        widget.bind('<Control-c>', copy_tree_selection)
        widget.bind('<Control-C>', copy_tree_selection)
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Копировать", command=copy_tree_selection)
        def show_menu(event):
            widget.selection_set(widget.identify_row(event.y))
            menu.post(event.x_root, event.y_root)
        widget.bind('<Button-3>', show_menu)
