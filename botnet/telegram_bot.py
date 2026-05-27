import requests
import json
import threading
from utils.logger import log

try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except:
    VOICE_AVAILABLE = False

class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.running = True
        self.voice_commands = {
            'атака': self._cmd_attack,
            'стоп': self._cmd_stop,
            'статус': self._cmd_status
        }
        self.last_update_id = 0
        thread = threading.Thread(target=self.polling, daemon=True)
        thread.start()

    def polling(self):
        while self.running:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates"
                params = {'offset': self.last_update_id + 1, 'timeout': 30}
                resp = requests.get(url, params=params, timeout=35)
                if resp.status_code == 200:
                    for upd in resp.json()['result']:
                        self.last_update_id = upd['update_id']
                        self.process_update(upd)
            except Exception as e:
                log(f"[Telegram] Polling error: {e}")
                threading.Event().wait(5)

    def process_update(self, upd):
        if 'message' not in upd:
            return
        msg = upd['message']
        if 'voice' in msg and VOICE_AVAILABLE:
            self._process_voice(msg)
        elif 'text' in msg:
            text = msg['text'].strip().lower()
            self._process_text(text)

    def _process_voice(self, msg):
        file_id = msg['voice']['file_id']
        file_info = requests.get(f"https://api.telegram.org/bot{self.token}/getFile?file_id={file_id}").json()
        file_path = file_info['result']['file_path']
        file_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
        audio_data = requests.get(file_url).content
        with open("voice.ogg", "wb") as f:
            f.write(audio_data)
        # Конвертация и распознавание
        r = sr.Recognizer()
        with sr.AudioFile("voice.ogg") as source:
            audio = r.record(source)
        try:
            text = r.recognize_google(audio, language="ru-RU").lower()
            self._process_text(text)
            self.send_message(f"Распознано: {text}")
        except Exception as e:
            self.send_message("Не удалось распознать голос")

    def _process_text(self, text):
        for cmd, func in self.voice_commands.items():
            if cmd in text:
                func(text)
                break
        else:
            self.send_message(f"Команда не распознана: {text}")

    def _cmd_attack(self, text):
        # Извлекаем цель
        parts = text.split()
        if len(parts) >= 2:
            target = parts[1]
            self.send_message(f"Запускаю атаку на {target}")
            # Здесь можно реально запустить атаку через движок
        else:
            self.send_message("Укажите цель: атака example.com")

    def _cmd_stop(self, text):
        self.send_message("Останавливаю все атаки")

    def _cmd_status(self, text):
        from engine.attack import stats
        mbps, active = asyncio.run(stats.get_stats())
        self.send_message(f"Активных атак: {active}, Трафик: {mbps:.2f} Mbps")

    def send_message(self, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            log(f"[Telegram] Ошибка отправки: {e}")
