"""Тесты подготовки данных и взаимодействия с базой."""

from datetime import date
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock, call

import main as app
import psycopg2
import pytest
from psycopg2.extensions import connection as PgConnection


def _patch_logger(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Подменить файловый логгер тестовым объектом."""
    logger_mock = Mock()
    monkeypatch.setattr(app, "get_file_logger", Mock(return_value=logger_mock))
    return logger_mock


def _patch_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Подменить подготовку строк всех сущностей."""
    monkeypatch.setattr(app.NorthEmployee, "from_rows", Mock(return_value=[]))
    monkeypatch.setattr(app.NorthCustomer, "from_rows", Mock(return_value=[]))
    monkeypatch.setattr(app.NorthOrder, "from_rows", Mock(return_value=[]))


def test_get_db_config_reads_valid_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Корректный env-файл преобразуется в параметры psycopg2."""
    _patch_logger(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DB_HOST=localhost\nDB_PORT=5432\nDB_NAME=north\nDB_USER=postgres\nDB_PASSWORD=secret\n",
        encoding="utf-8",
    )

    assert app.get_db_config(env_file) == {
        "host": "localhost",
        "port": 5432,
        "dbname": "north",
        "user": "postgres",
        "password": "secret",
    }


def test_get_db_config_handles_read_error(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Ошибка чтения env-файла возвращает None."""
    _patch_logger(monkeypatch)
    monkeypatch.setattr(app, "dotenv_values", Mock(side_effect=OSError("read error")))

    assert app.get_db_config("broken.env") is None
    assert "Не удалось прочитать" in capsys.readouterr().out


def test_get_db_config_reports_missing_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Пустые и отсутствующие параметры отклоняются."""
    _patch_logger(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PASSWORD=   \n", encoding="utf-8")

    assert app.get_db_config(env_file) is None


def test_get_db_config_rejects_invalid_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Некорректный порт возвращает None."""
    _patch_logger(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DB_HOST=localhost\nDB_PORT=wrong\nDB_NAME=north\nDB_USER=postgres\nDB_PASSWORD=secret\n",
        encoding="utf-8",
    )

    assert app.get_db_config(env_file) is None


def test_connect_to_database_returns_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Успешное подключение возвращает объект соединения."""
    _patch_logger(monkeypatch)
    connection_mock = Mock()
    monkeypatch.setattr(app.psycopg2, "connect", Mock(return_value=connection_mock))

    assert app.connect_to_database({"dbname": "north"}) is connection_mock


@pytest.mark.parametrize(
    "error",
    [
        psycopg2.OperationalError("connection error"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid byte"),
    ],
)
def test_connect_to_database_handles_errors(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
) -> None:
    """Ошибки подключения преобразуются в None."""
    _patch_logger(monkeypatch)
    monkeypatch.setattr(app.psycopg2, "connect", Mock(side_effect=error))

    assert app.connect_to_database({"dbname": "north"}) is None


def test_insert_functions_write_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Функции записи передают правильные данные курсору."""
    _patch_logger(monkeypatch)
    connection_mock = MagicMock()
    connection = cast(PgConnection, connection_mock)
    cursor = connection_mock.cursor.return_value.__enter__.return_value
    employee_rows: list[tuple[str, str, str, date, str | None]] = [
        ("Nancy", "Davolio", "Sales Representative", date(1948, 12, 8), None)
    ]
    customer_rows = [("ALFKI", "Alfreds Futterkiste", "Maria Anders")]
    order_rows = [(10248, "ALFKI", 1, date(1996, 7, 4), "Reims")]

    assert app.insert_employees(connection, employee_rows) == 1
    assert app.insert_customers(connection, customer_rows) == 1
    assert app.insert_orders(connection, order_rows) == 1
    assert cursor.executemany.call_args_list == [
        call(app.EMPLOYEES_INSERT_SQL, employee_rows),
        call(app.CUSTOMERS_UPSERT_SQL, customer_rows),
        call(app.ORDERS_UPSERT_SQL, order_rows),
    ]


def test_insert_functions_ignore_empty_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Пустые списки не открывают курсор."""
    _patch_logger(monkeypatch)
    connection_mock = MagicMock()
    connection = cast(PgConnection, connection_mock)

    assert app.insert_employees(connection, []) == 0
    assert app.insert_customers(connection, []) == 0
    assert app.insert_orders(connection, []) == 0
    connection_mock.cursor.assert_not_called()


def test_north_employee_from_record_and_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Сотрудник создаётся из записи и преобразуется обратно в строку."""
    record = {
        "first_name": " Nancy ",
        "last_name": "Davolio",
        "title": "Sales Representative",
        "birth_date": "1948-12-08",
        "notes": " note ",
    }
    employee = app.NorthEmployee.from_record(record)
    monkeypatch.setattr(app.NorthEmployee, "load_from_csv", Mock(return_value=[employee]))

    assert employee.birth_date == date(1948, 12, 8)
    assert app.NorthEmployee.from_rows() == [("Nancy", "Davolio", "Sales Representative", date(1948, 12, 8), "note")]


@pytest.mark.parametrize(
    ("record", "message"),
    [
        ({"first_name": ""}, "обязательное поле"),
        (
            {
                "first_name": "Nancy",
                "last_name": "Davolio",
                "title": "Sales Representative",
                "birth_date": "wrong",
            },
            "YYYY-MM-DD",
        ),
    ],
)
def test_north_employee_rejects_invalid_record(record: dict[str, object], message: str) -> None:
    """Некорректные поля сотрудника отклоняются."""
    with pytest.raises(ValueError, match=message):
        app.NorthEmployee.from_record(record)


def test_north_employee_allows_empty_notes() -> None:
    """Пустое примечание преобразуется в None."""
    employee = app.NorthEmployee.from_record(
        {
            "first_name": "Nancy",
            "last_name": "Davolio",
            "title": "Sales Representative",
            "birth_date": "1948-12-08",
            "notes": " ",
        }
    )

    assert employee.notes is None


def test_north_customer_from_record_and_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Клиент создаётся из записи и преобразуется обратно в строку."""
    customer = app.NorthCustomer.from_record(
        {"customer_id": " ALFKI ", "company_name": "Alfreds Futterkiste", "contact_name": "Maria Anders"}
    )
    monkeypatch.setattr(app.NorthCustomer, "load_from_csv", Mock(return_value=[customer]))

    assert app.NorthCustomer.from_rows() == [("ALFKI", "Alfreds Futterkiste", "Maria Anders")]


def test_north_customer_rejects_missing_field() -> None:
    """Пустое обязательное поле клиента отклоняется."""
    with pytest.raises(ValueError, match="обязательное поле"):
        app.NorthCustomer.from_record({"customer_id": "ALFKI"})


def test_north_order_from_record_and_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Заказ создаётся из записи и преобразуется обратно в строку."""
    order = app.NorthOrder.from_record(
        {
            "order_id": "10248",
            "customer_id": "VINET",
            "employee_id": "5",
            "order_date": "1996-07-04",
            "ship_city": "Reims",
        }
    )
    monkeypatch.setattr(app.NorthOrder, "load_from_csv", Mock(return_value=[order]))

    assert app.NorthOrder.from_rows() == [(10248, "VINET", 5, date(1996, 7, 4), "Reims")]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("order_id", "wrong", "order_id"),
        ("employee_id", "wrong", "employee_id"),
        ("order_date", "wrong", "YYYY-MM-DD"),
        ("ship_city", "", "обязательное поле"),
    ],
)
def test_north_order_rejects_invalid_fields(field: str, value: str, message: str) -> None:
    """Некорректные поля заказа отклоняются."""
    record = {
        "order_id": "10248",
        "customer_id": "VINET",
        "employee_id": "5",
        "order_date": "1996-07-04",
        "ship_city": "Reims",
    }
    record[field] = value

    with pytest.raises(ValueError, match=message):
        app.NorthOrder.from_record(record)


def test_main_stops_when_config_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Без конфигурации подключение не выполняется."""
    _patch_rows(monkeypatch)
    monkeypatch.setattr(app, "get_db_config", Mock(return_value=None))
    connect_mock = Mock()
    monkeypatch.setattr(app, "connect_to_database", connect_mock)

    app.main()

    connect_mock.assert_not_called()


def test_main_stops_when_connection_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Без соединения запись не выполняется."""
    _patch_rows(monkeypatch)
    monkeypatch.setattr(app, "get_db_config", Mock(return_value={"dbname": "north"}))
    monkeypatch.setattr(app, "connect_to_database", Mock(return_value=None))
    insert_mock = Mock()
    monkeypatch.setattr(app, "insert_employees", insert_mock)

    app.main()

    insert_mock.assert_not_called()


def test_main_writes_all_tables(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Успешный сценарий записывает все таблицы и закрывает соединение."""
    _patch_rows(monkeypatch)
    logger_mock = _patch_logger(monkeypatch)
    connection_mock = MagicMock()
    monkeypatch.setattr(app, "get_db_config", Mock(return_value={"dbname": "north"}))
    monkeypatch.setattr(app, "connect_to_database", Mock(return_value=connection_mock))
    monkeypatch.setattr(app, "insert_employees", Mock(return_value=9))
    monkeypatch.setattr(app, "insert_customers", Mock(return_value=91))
    monkeypatch.setattr(app, "insert_orders", Mock(return_value=830))

    app.main()

    connection_mock.close.assert_called_once_with()
    logger_mock.info.assert_called()
    assert "employees — 9" in capsys.readouterr().out


def test_main_handles_database_error(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Ошибка записи логируется, а соединение закрывается."""
    _patch_rows(monkeypatch)
    _patch_logger(monkeypatch)
    connection_mock = MagicMock()
    monkeypatch.setattr(app, "get_db_config", Mock(return_value={"dbname": "north"}))
    monkeypatch.setattr(app, "connect_to_database", Mock(return_value=connection_mock))
    monkeypatch.setattr(app, "insert_employees", Mock(side_effect=psycopg2.DatabaseError("write error")))

    app.main()

    connection_mock.close.assert_called_once_with()
    assert "Ошибка записи данных" in capsys.readouterr().out
