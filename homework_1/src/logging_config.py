"""Общая настройка файлового логирования модулей проекта."""

import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s"


def get_file_logger(name: str) -> logging.Logger:
    """Получить файловый логгер с перезаписью лога при первом вызове.

    Повторные вызовы с тем же именем возвращают уже настроенный логгер и не
    добавляют дублирующие обработчики.

    Args:
        name: Имя логгера и файла без расширения.

    Returns:
        Настроенный экземпляр ``logging.Logger``.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(LOG_DIR / f"{name}.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    return logger
