#!/usr/bin/env python3
# AVZ-Aristo RAGE – главный запускатор с автообновлением
import sys, os, json, subprocess, threading, time
try:
    import requests
except ImportError:
    print("Установите requests: pip install requests")
    sys.exit(1)
import tkinter as tk
from tkinter import messagebox
from gui.app import App

GITHUB_REPO = "Aristocrat702/avz"
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

# Загружаем версию
VERSION = "unknown"
if os.path.exists("version.json"):
    with open("version.json") as f:
        VERSION = json.load(f).get("version", "unknown")

def check_for_updates():
    try:
        resp = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/commits/main", timeout=5)
        if resp.status_code == 200:
            latest_sha = resp.json()['sha']
            if os.path.exists(".last_commit"):
                with open(".last_commit") as f:
                    saved_sha = f.read().strip()
                if saved_sha == latest_sha:
                    return False
            with open(".last_commit", "w") as f:
                f.write(latest_sha)
            return True
    except:
        pass
    return False

def update_from_github():
    try:
        subprocess.run(["git", "pull"], check=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        print("Обновлено через git pull")
        return True
    except:
        pass
    try:
        resp = requests.get(f"{RAW_URL}/manifest.json")
        if resp.status_code == 200:
            with open("manifest.json", "w") as f:
                f.write(resp.text)
            subprocess.run(["python", "update.py"], check=True)
            print("Обновлено через manifest.json")
            return True
    except:
        pass
    return False

if __name__ == "__main__":
    root = tk.Tk()
    root.title(f"AVZ-Aristo v{VERSION} RAGE")
    root.geometry("1200x800")

    def check_and_prompt():
        if check_for_updates():
            if messagebox.askyesno("Обновление", "Доступна новая версия программы. Обновить сейчас?"):
                if update_from_github():
                    messagebox.showinfo("Успех", "Программа обновлена. Перезапустите её.")
                    sys.exit(0)

    threading.Thread(target=check_and_prompt, daemon=True).start()

    app = App(root)
    root.mainloop()
