import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading, json, socket, requests, ssl, whois, dns.resolver, urllib.parse
from datetime import datetime

class ReconTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        # notebook.add(self.frame, text="Разведка")  # удалено
        self._create_widgets()

    def _create_widgets(self):
        # ... (весь остальной код без изменений)
        pass
