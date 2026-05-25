import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os, json, threading
from gui.widgets import RightClickMenu

class LootTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Трофеи (loot)", font=("Arial", 12, "bold")).pack(anchor='w')

        self.listbox = tk.Listbox(main, bg='white')
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        RightClickMenu(self.listbox, get_text_func=lambda: self.listbox.get(tk.ACTIVE))
        ttk.Button(main, text="Обновить", command=self.refresh).pack(pady=2)
        self.content = scrolledtext.ScrolledText(main, height=10, bg='white')
        self.content.pack(fill=tk.BOTH, expand=True)
        RightClickMenu(self.content)
        self.listbox.bind('<<ListboxSelect>>', self.show_content)

    def refresh(self):
        loot_dir = self.app.settings.get("loot_dir", "loot")
        if not os.path.exists(loot_dir):
            os.makedirs(loot_dir, exist_ok=True)
        self.listbox.delete(0, tk.END)
        for f in os.listdir(loot_dir):
            self.listbox.insert(tk.END, f)

    def show_content(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        filename = self.listbox.get(sel[0])
        loot_dir = self.app.settings.get("loot_dir", "loot")
        path = os.path.join(loot_dir, filename)
        self.content.delete(1.0, tk.END)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.content.insert(tk.END, f.read())
        except Exception as e:
            self.content.insert(tk.END, f"Ошибка чтения: {e}")
