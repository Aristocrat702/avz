import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from ai_connector import request_improvement, check_connection
import threading

class AIEngineerTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        ttk.Label(self, text="AI-Инженер v2.0", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=5)
        ttk.Label(status_frame, text="Статус VPS:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Проверка...")
        self.status_label.pack(side=tk.LEFT)
        ttk.Button(status_frame, text="Проверить связь", command=self.check_vps).pack(side=tk.RIGHT)
        self.check_vps()
        
        ttk.Label(self, text="Запрос к локальному AI (DeepSeek):").pack(anchor=tk.W, padx=5, pady=5)
        self.desc_entry = tk.Text(self, height=4)
        self.desc_entry.pack(fill=tk.X, padx=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5)
        self.send_btn = ttk.Button(btn_frame, text="Отправить на VPS", command=self.send_request)
        self.send_btn.pack(side=tk.LEFT, padx=2)
        self.local_btn = ttk.Button(btn_frame, text="Спросить локально", command=self.ask_local_ai)
        self.local_btn.pack(side=tk.LEFT, padx=2)
        
        self.output = scrolledtext.ScrolledText(self, height=10, state=tk.NORMAL)
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def check_vps(self):
        threading.Thread(target=self._check).start()

    def _check(self):
        alive = check_connection()
        self.status_label.config(text="Доступен" if alive else "Недоступен", foreground="green" if alive else "red")

    def send_request(self):
        desc = self.desc_entry.get("1.0", tk.END).strip()
        if not desc:
            messagebox.showwarning("Пусто", "Опишите, что нужно сделать")
            return
        self.send_btn.config(state=tk.DISABLED)
        self.output.insert(tk.END, f"Запрос: {desc}\nОжидание ответа от VPS...\n")
        threading.Thread(target=self._send, args=(desc,)).start()

    def _send(self, desc):
        result = request_improvement(desc)
        self.output.insert(tk.END, f"Ответ: {result.get('message', 'Неизвестно')}\n")
        if result.get('status') == 'ok':
            self.output.insert(tk.END, "Манифест применён!\n")
        self.send_btn.config(state=tk.NORMAL)

    def ask_local_ai(self):
        desc = self.desc_entry.get("1.0", tk.END).strip()
        if not desc:
            messagebox.showwarning("Пусто", "Опишите проблему")
            return
        # Здесь должна быть интеграция с локальной LLM (DeepSeek API)
        # Пока заглушка
        self.output.insert(tk.END, f"[Локальный AI] Анализирую запрос: {desc}\n")
        # В реальности отправляем запрос к локальному DeepSeek и получаем ответ
        self.output.insert(tk.END, "[AI] Рекомендую проверить логи и запустить автотесты.\n")
