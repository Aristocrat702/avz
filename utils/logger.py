import logging
import sys

class Logger:
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            fh = logging.FileHandler('avz.log')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def debug(self, message: str) -> None:
        self.logger.debug(message)


def log(message: str, level: str = 'info') -> None:
    if level == 'warning':
        logging.warning(message)
    elif level == 'error':
        logging.error(message)
    else:
        logging.info(message)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('avz.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
