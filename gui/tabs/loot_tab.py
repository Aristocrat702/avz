import tkinter as tk
from tkinter import scrolledtext
import os

class LootTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        self.text = scrolledtext.ScrolledText(self, width=80, height=20)
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.load_loot()

    def load_loot(self):
        loot_dir = "loot"
        if not os.path.exists(loot_dir):
            self.text.insert(tk.END, "Папка loot пуста.")
            return
        for fname in os.listdir(loot_dir):
            fpath = os.path.join(loot_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath, "r", errors="ignore") as f:
                    content = f.read()[:500]
                self.text.insert(tk.END, f"--- {fname} ---\n{content}\n\n")
