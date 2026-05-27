import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import json
import asyncio
from botnet.ssh_manager import SSHManager

class SSHTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.ssh = SSHManager()
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="Управление SSH узлами").pack()
        self.text = scrolledtext.ScrolledText(self, width=80, height=20)
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        btn_frame = tk.Frame(self)
        btn_frame.pack()
        tk.Button(btn_frame, text="Обновить список", command=self.refresh).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Выполнить команду", command=self.run_command).pack(side=tk.LEFT, padx=5)
        self.refresh()

    def refresh(self):
        self.text.delete(1.0, tk.END)
        for node in self.ssh.nodes:
            self.text.insert(tk.END, f"{node['host']} ({node.get('user','root')})\n")

    def run_command(self):
        host = simpledialog.askstring("SSH", "Хост:")
        cmd = simpledialog.askstring("SSH", "Команда:")
        if not host or not cmd:
            return
        node = next((n for n in self.ssh.nodes if n['host'] == host), None)
        if not node:
            messagebox.showerror("Ошибка", "Узел не найден")
            return
        async def exec_cmd():
            result = await self.ssh.execute(node['host'], node['user'], node['password'], cmd)
            self.text.insert(tk.END, f"Результат {host}:\n{result}\n")
        asyncio.run(exec_cmd())
