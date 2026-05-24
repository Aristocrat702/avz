import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

class TelegramBot:
    def __init__(self, token, chat_id, app=None):
        self.token = token
        self.chat_id = chat_id
        self.app = app
        self.application = None

    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("AVZ-Aristo бот активен. /status /attack <target> <method> <threads>")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.app and hasattr(self.app, 'attack_tab'):
            status = "Атака активна" if self.app.attack_tab.attack_active else "Атака неактивна"
        else:
            status = "статус неизвестен"
        await update.message.reply_text(status)

    async def attack(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or len(context.args) < 3:
            await update.message.reply_text("Использование: /attack <target> <method> <threads>")
            return
        target = context.args[0]
        method = context.args[1]
        threads = int(context.args[2])
        if self.app and hasattr(self.app, 'attack_tab'):
            tab = self.app.attack_tab
            tab.target_entry.delete(0, 'end')
            tab.target_entry.insert(0, target)
            tab.method_var.set(method)
            tab.threads_var.set(threads)
            tab._start_attack()
            await update.message.reply_text(f"Атака запущена: {target} {method} {threads}")
        else:
            await update.message.reply_text("Нет доступа к интерфейсу атаки")

    def run(self):
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start_cmd))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("attack", self.attack))
        threading.Thread(target=self.application.run_polling, daemon=True).start()