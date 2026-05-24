import tkinter as tk
from tkinter import ttk, scrolledtext
import os, json

class LootTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        # notebook.add(self.frame, text="Трофеи")  # удалено
        self._create_widgets()

    def _create_widgets(self):
        # ... (весь остальной код без изменений)
        pass
