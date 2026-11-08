"""Абстракции для работы с данными заказов."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Self

from src.logging_config import get_file_logger
from src.reads import Transaction, get_transactions_from_csv

DEFAULT_ORDERS_FILE = Path(__file__).resolve().parent.parent / "north_data" / "orders_data.csv"


@dataclass(slots=True)
class Order(ABC):
    """Абстрактное представление заказа."""

    order_id: int
    customer_id: str
    employee_id: int
    order_date: date
    ship_city: str

    @classmethod
    def load_from_csv(cls, file_path: str | Path = DEFAULT_ORDERS_FILE) -> list[Self]:
        """Загрузить заказы из CSV-файла через модуль ``reads``.

        Args:
            file_path: Путь к CSV-файлу с данными заказов.

        Returns:
            Список экземпляров конкретного класса-наследника. Если файл
            отсутствует или не может быть прочитан, возвращается пустой список.
        """
        logger = get_file_logger("orders")
        logger.debug("Начало загрузки заказов из файла %s", file_path)
        records = get_transactions_from_csv(file_path, delimiter=",")
        orders: list[Self] = []
        skipped_records = 0

        for row_number, record in enumerate(records, start=2):
            try:
                orders.append(cls.from_record(record))
            except (TypeError, ValueError) as error:
                skipped_records += 1
                logger.warning("Строка %d пропущена: %s", row_number, error)
                continue

        logger.info(
            "Загрузка заказов завершена: загружено — %d, пропущено — %d",
            len(orders),
            skipped_records,
        )
        return orders

    @classmethod
    @abstractmethod
    def from_record(cls, record: Transaction) -> Self:
        """Создать экземпляр конкретного класса из CSV-записи."""

    @classmethod
    @abstractmethod
    def from_rows(cls) -> list[tuple[int, str, int, date, str]]:
        """Вернуть строки для записи в таблицу."""
