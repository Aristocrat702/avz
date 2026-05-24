import logging
import os
from datetime import datetime

LOG_FILE = "avz.log"
MAX_LOG_SIZE = 2 * 1024 * 1024  # 2 МБ

class AppLogger:
    def __init__(self, name="AVZ-Aristo"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        # Файловый обработчик
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        # Ротация размера (упрощённая)
        self.check_rotate()

    def check_rotate(self):
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
            backup = LOG_FILE + ".1"
            if os.path.exists(backup):
                os.remove(backup)
            os.rename(LOG_FILE, backup)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def debug(self, msg):
        self.logger.debug(msg)
