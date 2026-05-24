# utils/logger.py
import logging

class Logger:
    def __init__(self, log_file='avz.log'):
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            encoding='utf-8'
        )
        self.logger = logging.getLogger('AVZ')

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def warning(self, msg):
        self.logger.warning(msg)