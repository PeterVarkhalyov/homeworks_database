"""Тесты абстрактных моделей CSV-сущностей."""

from datetime import date
from pathlib import Path
from typing import Self
from unittest.mock import Mock

import pytest
from src import Customer, Employee, Order
from src import customers as customers_module
from src import employees as employees_module
from src import orders as orders_module
from src.reads import Transaction


class ConcreteEmployee(Employee):
    """Тестовая реализация сотрудника."""

    @classmethod
    def from_record(cls, record: Transaction) -> Self:
        if record.get("invalid"):
            raise ValueError("invalid employee")
        return cls("Nancy", "Davolio", "Sales Representative", date(1948, 12, 8), None)

    @classmethod
    def from_rows(cls) -> list[tuple[str, str, str, date, str | None]]:
        return []


class ConcreteCustomer(Customer):
    """Тестовая реализация клиента."""

    @classmethod
    def from_record(cls, record: Transaction) -> Self:
        if record.get("invalid"):
            raise TypeError("invalid customer")
        return cls("ALFKI", "Alfreds Futterkiste", "Maria Anders")

    @classmethod
    def from_rows(cls) -> list[tuple[str, str, str]]:
        return []


class ConcreteOrder(Order):
    """Тестовая реализация заказа."""

    @classmethod
    def from_record(cls, record: Transaction) -> Self:
        if record.get("invalid"):
            raise ValueError("invalid order")
        return cls(10248, "ALFKI", 1, date(1996, 7, 4), "Reims")

    @classmethod
    def from_rows(cls) -> list[tuple[int, str, int, date, str]]:
        return []


@pytest.mark.parametrize(
    ("module", "model", "entity_name"),
    [
        (employees_module, ConcreteEmployee, "employees"),
        (customers_module, ConcreteCustomer, "customers"),
        (orders_module, ConcreteOrder, "orders"),
    ],
)
def test_load_from_csv_skips_invalid_records(
    module: object,
    model: type[Employee] | type[Customer] | type[Order],
    entity_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Модели загружают корректную запись и пропускают ошибочную."""
    logger_mock = Mock()
    get_logger_mock = Mock(return_value=logger_mock)
    read_mock = Mock(return_value=[{"valid": True}, {"invalid": True}])
    monkeypatch.setattr(module, "get_file_logger", get_logger_mock)
    monkeypatch.setattr(module, "get_transactions_from_csv", read_mock)
    csv_file = tmp_path / "data.csv"

    result = model.load_from_csv(csv_file)

    assert len(result) == 1
    get_logger_mock.assert_called_once_with(entity_name)
    read_mock.assert_called_once_with(csv_file, delimiter=",")
    logger_mock.warning.assert_called_once()
    logger_mock.info.assert_called_once()
