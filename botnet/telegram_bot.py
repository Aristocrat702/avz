import requests
import json
from utils.logger import log

class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send_message(self, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            log(f"[Telegram] Ошибка отправки: {e}")

    def check_bot(self):
        url = f"https://api.telegram.org/bot{self.token}/getMe"
        try:
            resp = requests.get(url)
            if resp.ok:
                return resp.json()['result']['username']
        except:
            pass
        return None
