"""Тесты общей настройки логирования."""

import logging
from pathlib import Path

import pytest
from src import logging_config


def test_get_file_logger_creates_and_reuses_file_handler(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Логгер создаёт файл и не добавляет повторный обработчик."""
    monkeypatch.setattr(logging_config, "LOG_DIR", tmp_path)
    logger_name = f"test_{tmp_path.name}"
    logger = logging.getLogger(logger_name)
    logger.handlers.clear()

    try:
        first_logger = logging_config.get_file_logger(logger_name)
        second_logger = logging_config.get_file_logger(logger_name)
        first_logger.info("test message")

        assert first_logger is second_logger
        assert first_logger.propagate is False
        assert len(first_logger.handlers) == 1
        assert "test message" in (tmp_path / f"{logger_name}.log").read_text(encoding="utf-8")
    finally:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
