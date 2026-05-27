import logging
import sys

# ---------- Класс Logger (используется GUI и старыми модулями) ----------
class Logger:
    def __init__(self, name=__name__):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            # Пишем также в файл
            fh = logging.FileHandler('avz.log')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def debug(self, message):
        self.logger.debug(message)


# ---------- Глобальная функция log (используется новыми модулями) ----------
def log(message: str):
    """Простая функция логирования, которую ожидают spreader, c2 и т.д."""
    logging.info(message)
    print(message)


# Настройка корневого логгера, чтобы функция log работала
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('avz.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
