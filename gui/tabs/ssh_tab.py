import tkinter as tk
from tkinter import ttk, messagebox
import threading, socket, paramiko

class SSHTab(ttk.Frame):
    def __init__(self, parent, app=None):
        super().__init__(parent)
        self.app = app
        self.create_widgets()

    def create_widgets(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="SSH-серверы (свои узлы)", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=4, pady=5)

        ttk.Label(main, text="IP:Port").grid(row=1, column=0, sticky='w')
        self.ip_entry = ttk.Entry(main, width=18)
        self.ip_entry.grid(row=1, column=1, padx=5)
        ttk.Label(main, text="User").grid(row=1, column=2, sticky='w')
        self.user_entry = ttk.Entry(main, width=12)
        self.user_entry.grid(row=1, column=3, padx=5)
        ttk.Label(main, text="Pass").grid(row=1, column=4, sticky='w')
        self.pass_entry = ttk.Entry(main, width=12, show="*")
        self.pass_entry.grid(row=1, column=5, padx=5)

        ttk.Button(main, text="Добавить", command=self.add_node).grid(row=2, column=0, columnspan=6, pady=5)

        self.tree = ttk.Treeview(main, columns=("ip", "user", "status"), show="headings", height=8)
        self.tree.heading("ip", text="IP:Port")
        self.tree.heading("user", text="User")
        self.tree.heading("status", text="Статус")
        self.tree.column("ip", width=160)
        self.tree.column("user", width=100)
        self.tree.column("status", width=80)
        self.tree.grid(row=3, column=0, columnspan=6, pady=10, sticky='nsew')

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=4, column=0, columnspan=6, pady=5)
        ttk.Button(btn_frame, text="Удалить", command=self.del_node).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Проверить", command=self.check_node).pack(side=tk.LEFT, padx=5)

    def add_node(self):
        ip = self.ip_entry.get().strip()
        user = self.user_entry.get().strip()
        passwd = self.pass_entry.get().strip()
        if not ip or not user:
            messagebox.showwarning("Ошибка", "Введите IP и пользователя")
            return
        self.tree.insert("", "end", values=(ip, user, "unknown"))
        self.ip_entry.delete(0, tk.END)
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)

    def del_node(self):
        for item in self.tree.selection():
            self.tree.delete(item)

    def check_node(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите узел")
            return
        item = selected[0]
        ip, user, _ = self.tree.item(item, 'values')
        passwd = self.pass_entry.get()  # упрощённо – пароль берётся из поля
        def check():
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=user, password=passwd, timeout=3)
                client.close()
                self.tree.set(item, "status", "online")
            except:
                self.tree.set(item, "status", "offline")
        threading.Thread(target=check, daemon=True).start()
