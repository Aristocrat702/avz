import tkinter as tk
from tkinter import ttk, scrolledtext

def enable_clipboard_copy(widget, get_text_func=None):
    menu = tk.Menu(widget, tearoff=0)
    def copy_to_clipboard():
        try:
            if get_text_func:
                text = get_text_func()
            else:
                text = widget.selection_get() if hasattr(widget, 'selection_get') else widget.get(1.0, tk.END)
            widget.clipboard_clear()
            widget.clipboard_append(text)
        except:
            pass
    menu.add_command(label="Копировать", command=copy_to_clipboard)
    def paste_from_clipboard():
        try:
            text = widget.clipboard_get()
            if isinstance(widget, tk.Text):
                widget.insert(tk.INSERT, text)
            elif isinstance(widget, tk.Entry):
                widget.insert(tk.INSERT, text)
            elif isinstance(widget, ttk.Entry):
                widget.insert(tk.INSERT, text)
        except:
            pass
    menu.add_command(label="Вставить", command=paste_from_clipboard)
    def show_menu(event):
        menu.post(event.x_root, event.y_root)
    widget.bind('<Button-3>', show_menu)
    widget.bind('<Control-c>', lambda e: copy_to_clipboard())
    widget.bind('<Control-C>', lambda e: copy_to_clipboard())
    widget.bind('<Control-v>', lambda e: paste_from_clipboard())
    widget.bind('<Control-V>', lambda e: paste_from_clipboard())

def enable_global_clipboard(root):
    def recurse(widget):
        if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
            enable_clipboard_copy(widget, lambda: widget.selection_get() if widget.tag_ranges(tk.SEL) else widget.get(1.0, tk.END))
        elif isinstance(widget, (tk.Entry, ttk.Entry)):
            enable_clipboard_copy(widget, lambda: widget.selection_get() if widget.selection_present() else widget.get())
        elif isinstance(widget, ttk.Treeview):
            enable_clipboard_copy(widget, lambda: json.dumps([widget.item(i, 'values') for i in widget.selection()]) if widget.selection() else "")
        elif isinstance(widget, tk.Listbox):
            enable_clipboard_copy(widget, lambda: "\n".join([widget.get(i) for i in widget.curselection()]))
        for child in widget.winfo_children():
            recurse(child)
    recurse(root)
