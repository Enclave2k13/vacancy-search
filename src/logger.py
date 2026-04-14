"""Настройка логирования для всего проекта"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "vacancy_search", log_file: str = "app.log") -> logging.Logger:
    """
    Настраивает и возвращает логгер с указанным именем

    Args:
        name: имя логгера
        log_file: путь к файлу логов

    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    log_path = Path(log_file)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    if logger.handlers:
        logger.handlers.clear()

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


app_logger = setup_logger()