import tkinter as tk

def enable_clipboard_copy(widget):
    """Делает так, чтобы Ctrl+C копировал выделенный текст в буфер обмена."""
    if isinstance(widget, tk.Text):
        widget.bind('<Control-c>', lambda e: widget.event_generate('<<Copy>>'))
    elif isinstance(widget, tk.Entry):
        widget.bind('<Control-c>', lambda e: widget.event_generate('<<Copy>>'))
    elif isinstance(widget, ttk.Entry):
        widget.bind('<Control-c>', lambda e: widget.event_generate('<<Copy>>'))
    elif isinstance(widget, tk.Listbox):
        widget.bind('<Control-c>', lambda e: _copy_listbox_selection(widget))
    elif isinstance(widget, ttk.Treeview):
        widget.bind('<Control-c>', lambda e: _copy_treeview_selection(widget))

def _copy_listbox_selection(listbox):
    sel = listbox.curselection()
    if sel:
        text = '\n'.join([listbox.get(i) for i in sel])
        listbox.clipboard_clear()
        listbox.clipboard_append(text)

def _copy_treeview_selection(tree):
    sel = tree.selection()
    if sel:
        rows = []
        for iid in sel:
            values = tree.item(iid, 'values')
            rows.append('\t'.join(map(str, values)))
        text = '\n'.join(rows)
        tree.clipboard_clear()
        tree.clipboard_append(text)
