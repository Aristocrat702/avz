import tkinter as tk
from tkinter import ttk, messagebox
from botnet.telegram_bot import TelegramBot
from gui.widgets import RightClickMenu

class TelegramTab:
    def __init__(self, notebook, app):
        self.app = app
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="✈️ Telegram")
        self.telegram_bot = None
        self._build_ui()
        self.app.logger.info("Вкладка Telegram инициализирована")

    def _build_ui(self):
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        main = ttk.LabelFrame(self.frame, text="Настройки Telegram бота", padding=10)
        main.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        ttk.Label(main, text="Токен:").grid(row=0, column=0, sticky='w')
        self.tg_token = ttk.Entry(main, width=50)
        self.tg_token.grid(row=0, column=1, padx=5)
        ttk.Label(main, text="Chat ID:").grid(row=1, column=0, sticky='w')
        self.tg_chat = ttk.Entry(main, width=50)
        self.tg_chat.grid(row=1, column=1, padx=5)
        ttk.Button(main, text="▶ Запустить бота", command=self._start_telegram).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(main, text="⏹ Остановить бота", command=self._stop_telegram).grid(row=3, column=0, columnspan=2, pady=5)
        # Лог
        self.log_text = tk.Text(self.frame, height=10, bg='#1e1e1e' if self.app.theme=='dark' else 'white',
                                fg='lime' if self.app.theme=='dark' else 'black')
        self.log_text.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        RightClickMenu(self.log_text, get_text_func=lambda: self.log_text.get("1.0", tk.END).strip())

    def _log(self, msg):
        self.log_text.insert(tk.END, msg)
        self.log_text.see(tk.END)

    def _start_telegram(self):
        token = self.tg_token.get().strip()
        chat = self.tg_chat.get().strip()
        if not token or not chat:
            messagebox.showerror("Ошибка", "Введите токен и Chat ID")
            return
        try:
            self.telegram_bot = TelegramBot(token, chat, self.app)
            self.telegram_bot.run()
            self._log("[TG] Бот запущен\n")
            messagebox.showinfo("Успех", "Telegram бот активирован")
        except Exception as e:
            self._log(f"[TG] Ошибка: {e}\n")
            messagebox.showerror("Ошибка", str(e))

    def _stop_telegram(self):
        if self.telegram_bot:
            self.telegram_bot = None
            self._log("[TG] Бот остановлен\n")
