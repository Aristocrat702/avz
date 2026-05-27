import logging
import sys

# Простая функция логирования, которую ожидают все модули
def log(message: str):
    """Запись сообщения в лог-файл avz.log и вывод на консоль."""
    logging.info(message)
    print(message)

# Настройка логирования один раз при импорте
logging.basicConfig(
    filename='avz.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
