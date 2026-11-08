"""Абстракции для работы с данными сотрудников."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Self

from src.logging_config import get_file_logger
from src.reads import Transaction, get_transactions_from_csv

DEFAULT_EMPLOYEES_FILE = Path(__file__).resolve().parent.parent / "north_data" / "employees_data.csv"


@dataclass(slots=True)
class Employee(ABC):
    """Абстрактное представление сотрудника."""

    first_name: str
    last_name: str
    title: str
    birth_date: date
    notes: str | None

    @classmethod
    def load_from_csv(cls, file_path: str | Path = DEFAULT_EMPLOYEES_FILE) -> list[Self]:
        """Загрузить сотрудников из CSV-файла через модуль ``reads``.

        Args:
            file_path: Путь к CSV-файлу с данными сотрудников.

        Returns:
            Список экземпляров конкретного класса-наследника. Если файл
            отсутствует или не может быть прочитан, возвращается пустой список.
            Записи с отсутствующими или некорректными полями пропускаются.
        """
        logger = get_file_logger("employees")
        logger.debug("Начало загрузки сотрудников из файла %s", file_path)
        records = get_transactions_from_csv(file_path, delimiter=",")
        employees: list[Self] = []
        skipped_records = 0

        for row_number, record in enumerate(records, start=2):
            try:
                employees.append(cls.from_record(record))
            except (TypeError, ValueError) as error:
                skipped_records += 1
                logger.warning("Строка %d пропущена: %s", row_number, error)
                continue

        logger.info(
            "Загрузка сотрудников завершена: загружено — %d, пропущено — %d",
            len(employees),
            skipped_records,
        )
        return employees

    @classmethod
    @abstractmethod
    def from_record(cls, record: Transaction) -> Self:
        """Создать экземпляр конкретного класса из CSV-записи."""

    @classmethod
    @abstractmethod
    def from_rows(cls) -> list[tuple[str, str, str, date, str | None]]:
        """Вернуть строки сотрудников для записи в таблицу."""
