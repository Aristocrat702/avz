#!/usr/bin/env python3
# AVZ-Aristo RAGE – главный запускатор
import sys
import argparse
import tkinter as tk
from gui.app import App

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AVZ-Aristo RAGE")
    parser.add_argument("--c2", action="store_true", help="Запустить C2 локально")
    args = parser.parse_args()

    if args.c2:
        print("[*] Локальный C2 не реализован, используйте VPS")
        sys.exit(0)

    root = tk.Tk()
    app = App(root)
    root.mainloop()
