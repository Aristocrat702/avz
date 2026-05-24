import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os

class SettingsTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        # notebook.add(self.frame, text="Настройки")  # удалено
        self._create_widgets()

    def _create_widgets(self):
        # ... (весь остальной код без изменений)
        pass
