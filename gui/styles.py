import tkinter as tk
from tkinter import ttk

def apply_theme(root, theme):
    style = ttk.Style()
    style.theme_use('clam')
    colors = theme

    style.configure('.',
        background=colors['bg'],
        foreground=colors['fg'],
        fieldbackground=colors['entry_bg'],
        troughcolor=colors['progress_bg'],
        selectbackground=colors['select_bg'],
        selectforeground=colors['select_fg']
    )

    style.configure('TLabel',
        foreground=colors['label_fg'],
        background=colors['bg'],
        font=('Segoe UI', 9)
    )

    style.configure('TButton',
        background=colors['button_bg'],
        foreground=colors['button_fg'],
        borderwidth=1,
        focusthickness=0,
        padding=6,
        font=('Segoe UI', 9, 'bold'),
        relief='raised'
    )
    style.map('TButton',
        background=[('active', colors['button_active_bg']), ('pressed', colors['button_active_bg'])],
        foreground=[('active', colors['button_active_fg']), ('pressed', colors['button_active_fg'])],
        relief=[('pressed', 'sunken')]
    )

    style.configure('TEntry',
        fieldbackground=colors['entry_bg'],
        foreground=colors['entry_fg'],
        insertcolor=colors['entry_insert'],
        padding=4
    )

    style.configure('TCombobox',
        fieldbackground=colors['entry_bg'],
        foreground=colors['entry_fg'],
        arrowcolor=colors['fg'],
        padding=4
    )
    style.map('TCombobox',
        fieldbackground=[('readonly', colors['entry_bg'])],
        foreground=[('readonly', colors['entry_fg'])]
    )

    style.configure('TProgressbar',
        background=colors['progress_color'],
        troughcolor=colors['progress_bg'],
        thickness=18
    )

    style.configure('Treeview',
        background=colors['tree_bg'],
        foreground=colors['tree_fg'],
        fieldbackground=colors['tree_bg'],
        font=('Segoe UI', 9)
    )
    style.configure('Treeview.Heading',
        background=colors['tree_heading_bg'],
        foreground=colors['tree_heading_fg'],
        font=('Segoe UI', 9, 'bold')
    )
    style.map('Treeview',
        background=[('selected', colors['tree_selected_bg'])],
        foreground=[('selected', colors['tree_selected_fg'])]
    )

    style.configure('TNotebook',
        background=colors['bg'],
        borderwidth=0
    )
    style.configure('TNotebook.Tab',
        background=colors['button_bg'],
        foreground=colors['button_fg'],
        padding=[12, 4],
        borderwidth=0,
        font=('Segoe UI', 9, 'bold')
    )
    style.map('TNotebook.Tab',
        background=[('selected', colors['select_bg'])],
        foreground=[('selected', colors['select_fg'])]
    )

    style.configure('TFrame',
        background=colors['bg']
    )
    style.configure('TLabelframe',
        background=colors['bg'],
        foreground=colors['fg'],
        font=('Segoe UI', 9, 'bold')
    )
    style.configure('TLabelframe.Label',
        foreground=colors['fg']
    )
