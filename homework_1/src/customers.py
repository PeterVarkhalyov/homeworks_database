"""Абстракции для работы с данными клиентов."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from src.logging_config import get_file_logger
from src.reads import Transaction, get_transactions_from_csv

DEFAULT_CUSTOMERS_FILE = Path(__file__).resolve().parent.parent / "north_data" / "customers_data.csv"


@dataclass(slots=True)
class Customer(ABC):
    """Абстрактное представление клиента."""

    customer_id: str
    company_name: str
    contact_name: str

    @classmethod
    def load_from_csv(cls, file_path: str | Path = DEFAULT_CUSTOMERS_FILE) -> list[Self]:
        """Загрузить клиентов из CSV-файла через модуль ``reads``.

        Args:
            file_path: Путь к CSV-файлу с данными клиентов.

        Returns:
            Список экземпляров конкретного класса-наследника. Если файл
            отсутствует или не может быть прочитан, возвращается пустой список.
        """
        logger = get_file_logger("customers")
        logger.debug("Начало загрузки клиентов из файла %s", file_path)
        records = get_transactions_from_csv(file_path, delimiter=",")
        customers: list[Self] = []
        skipped_records = 0

        for row_number, record in enumerate(records, start=2):
            try:
                customers.append(cls.from_record(record))
            except (TypeError, ValueError) as error:
                skipped_records += 1
                logger.warning("Строка %d пропущена: %s", row_number, error)
                continue

        logger.info(
            "Загрузка клиентов завершена: загружено — %d, пропущено — %d",
            len(customers),
            skipped_records,
        )
        return customers

    @classmethod
    @abstractmethod
    def from_record(cls, record: Transaction) -> Self:
        """Создать экземпляр конкретного класса из CSV-записи."""

    @classmethod
    @abstractmethod
    def from_rows(cls) -> list[tuple[str, str, str]]:
        """Вернуть строки клиентов для записи в таблицу."""
