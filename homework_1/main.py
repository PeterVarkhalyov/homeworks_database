"""Получение данных сотрудников из CSV-файла."""

from datetime import date
from pathlib import Path
from typing import Any, Self, cast

import psycopg2
from dotenv import dotenv_values
from psycopg2.extensions import connection as PgConnection
from src import Customer, Employee, Order
from src.logging_config import get_file_logger
from src.reads import Transaction

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

DB_ENV_MAPPING = {
    "DB_HOST": "host",
    "DB_PORT": "port",
    "DB_NAME": "dbname",
    "DB_USER": "user",
    "DB_PASSWORD": "password",
}

EMPLOYEES_INSERT_SQL = """
    INSERT INTO public.employees (first_name, last_name, title, birth_date, notes)
    VALUES (%s, %s, %s, %s, %s)
"""

CUSTOMERS_UPSERT_SQL = """
    INSERT INTO public.customers (customer_id, company_name, contact_name)
    VALUES (%s, %s, %s)
    ON CONFLICT (customer_id) DO UPDATE SET
        company_name = EXCLUDED.company_name,
        contact_name = EXCLUDED.contact_name
"""

ORDERS_UPSERT_SQL = """
    INSERT INTO public.orders (order_id, customer_id, employee_id, order_date, ship_city)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (order_id) DO UPDATE SET
        customer_id = EXCLUDED.customer_id,
        employee_id = EXCLUDED.employee_id,
        order_date = EXCLUDED.order_date,
        ship_city = EXCLUDED.ship_city
"""


def get_db_config(env_path: str | Path = ENV_FILE) -> dict[str, Any] | None:
    """Прочитать и проверить параметры подключения из ``.env``.

    Args:
        env_path: Путь к файлу с параметрами подключения.

    Returns:
        Словарь параметров для ``psycopg2.connect`` либо ``None``, если файл
        недоступен или содержит некорректные данные.
    """
    logger = get_file_logger("main")
    env_path = Path(env_path)
    logger.debug("Начало чтения конфигурации подключения из %s", env_path)

    try:
        env_values = dotenv_values(env_path)
    except (OSError, UnicodeError) as error:
        message = f"Не удалось прочитать {env_path}: {error}"
        logger.error(message)
        print(message)
        return None

    config_values = {
        env_name: value.strip()
        for env_name in DB_ENV_MAPPING
        if (value := env_values.get(env_name)) is not None and value.strip()
    }
    missing = [env_name for env_name in DB_ENV_MAPPING if env_name not in config_values]

    if missing:
        message = f"В {env_path} не заданы параметры: {', '.join(missing)}"
        logger.error(message)
        print(message)
        return None

    try:
        port = int(config_values["DB_PORT"])
    except ValueError:
        message = "Параметр DB_PORT должен быть целым числом"
        logger.error(message)
        print(message)
        return None

    config: dict[str, Any] = {
        connection_key: config_values[env_name] for env_name, connection_key in DB_ENV_MAPPING.items()
    }
    config["port"] = port
    logger.info("Конфигурация подключения к базе данных успешно загружена")
    return config


def connect_to_database(config: dict[str, Any]) -> PgConnection | None:
    """Создать соединение с базой данных по проверенной конфигурации."""
    logger = get_file_logger("main")
    logger.debug("Начало подключения к базе данных")

    try:
        connection = psycopg2.connect(**config)
    except (psycopg2.Error, UnicodeDecodeError) as error:
        message = f"Ошибка подключения к базе данных: {error}"
        logger.error(message)
        print(message)
        return None

    logger.info("Подключение к базе данных успешно выполнено")
    return cast(PgConnection, connection)


def insert_employees(
    connection: PgConnection,
    rows: list[tuple[str, str, str, date, str | None]],
) -> int:
    """Добавить сотрудников в ``public.employees`` с автоматическим ID."""
    logger = get_file_logger("main")

    if not rows:
        logger.warning("Нет данных для записи в public.employees")
        return 0

    with connection.cursor() as cursor:
        cursor.executemany(EMPLOYEES_INSERT_SQL, rows)

    logger.info("В public.employees записано строк: %d", len(rows))
    return len(rows)


def insert_customers(connection: PgConnection, rows: list[tuple[str, str, str]]) -> int:
    """Добавить или обновить клиентов в ``public.customers``."""
    logger = get_file_logger("main")

    if not rows:
        logger.warning("Нет данных для записи в public.customers")
        return 0

    with connection.cursor() as cursor:
        cursor.executemany(CUSTOMERS_UPSERT_SQL, rows)

    logger.info("В public.customers записано строк: %d", len(rows))
    return len(rows)


def insert_orders(
    connection: PgConnection,
    rows: list[tuple[int, str, int, date, str]],
) -> int:
    """Добавить или обновить заказы в ``public.orders``."""
    logger = get_file_logger("main")

    if not rows:
        logger.warning("Нет данных для записи в public.orders")
        return 0

    with connection.cursor() as cursor:
        cursor.executemany(ORDERS_UPSERT_SQL, rows)

    logger.info("В public.orders записано строк: %d", len(rows))
    return len(rows)


class NorthEmployee(Employee):
    """Сотрудник North, создаваемый из CSV-записи."""

    @classmethod
    def from_record(cls, record: Transaction) -> Self:
        """Преобразовать CSV-запись в объект сотрудника."""
        required_fields = ("first_name", "last_name", "title", "birth_date")
        values: dict[str, str] = {}

        for field in required_fields:
            value = record.get(field)
            if value is None or not str(value).strip():
                raise ValueError(f"В employees_data.csv отсутствует обязательное поле {field}")
            values[field] = str(value).strip()

        try:
            birth_date = date.fromisoformat(values["birth_date"])
        except ValueError as error:
            raise ValueError("Поле birth_date должно иметь формат YYYY-MM-DD") from error

        notes_value = record.get("notes")
        notes = str(notes_value).strip() if notes_value is not None and str(notes_value).strip() else None

        return cls(
            first_name=values["first_name"],
            last_name=values["last_name"],
            title=values["title"],
            birth_date=birth_date,
            notes=notes,
        )

    @classmethod
    def from_rows(cls) -> list[tuple[str, str, str, date, str | None]]:
        """Подготовить данные сотрудников для записи в таблицу.

        Returns:
            Список кортежей следующей структуры:
            ``(first_name, last_name, title, birth_date, notes)``.
            Некорректные CSV-записи пропускаются методом ``load_from_csv``.
        """
        employees = cls.load_from_csv()
        return [
            (
                employee.first_name,
                employee.last_name,
                employee.title,
                employee.birth_date,
                employee.notes,
            )
            for employee in employees
        ]


class NorthCustomer(Customer):
    """Клиент North, создаваемый из CSV-записи."""

    @classmethod
    def from_record(cls, record: Transaction) -> Self:
        """Преобразовать CSV-запись в объект клиента."""
        required_fields = ("customer_id", "company_name", "contact_name")
        values: dict[str, str] = {}

        for field in required_fields:
            value = record.get(field)
            if value is None or not str(value).strip():
                raise ValueError(f"В customers_data.csv отсутствует обязательное поле {field}")
            values[field] = str(value).strip()

        return cls(
            customer_id=values["customer_id"],
            company_name=values["company_name"],
            contact_name=values["contact_name"],
        )

    @classmethod
    def from_rows(cls) -> list[tuple[str, str, str]]:
        """Подготовить данные сотрудников для записи в таблицу.

        Returns:
            Список кортежей следующей структуры:
            ``(first_name, last_name, title, birth_date, notes)``.
            Некорректные CSV-записи пропускаются методом ``load_from_csv``.
        """
        customers = cls.load_from_csv()
        return [
            (
                customer.customer_id,
                customer.company_name,
                customer.contact_name,
            )
            for customer in customers
        ]


class NorthOrder(Order):
    """Заказы North, создаваемый из CSV-записи."""

    @classmethod
    def from_record(cls, record: Transaction) -> Self:
        """Преобразовать CSV-запись в объект заказы."""
        required_fields = ("order_id", "customer_id", "employee_id", "order_date", "ship_city")
        values: dict[str, str] = {}

        for field in required_fields:
            value = record.get(field)
            if value is None or not str(value).strip():
                raise ValueError(f"В orders_data.csv отсутствует обязательное поле {field}")
            values[field] = str(value).strip()

        try:
            order_id = int(values["order_id"])
        except (TypeError, ValueError) as error:
            raise ValueError("Поле order_id должно быть целым числом") from error

        try:
            employee_id = int(values["employee_id"])
        except (TypeError, ValueError) as error:
            raise ValueError("Поле employee_id должно быть целым числом") from error

        try:
            order_date = date.fromisoformat(values["order_date"])
        except ValueError as error:
            raise ValueError("Поле order_date должно иметь формат YYYY-MM-DD") from error

        return cls(
            order_id=order_id,
            customer_id=values["customer_id"],
            employee_id=employee_id,
            order_date=order_date,
            ship_city=values["ship_city"],
        )

    @classmethod
    def from_rows(cls) -> list[tuple[int, str, int, date, str]]:
        """Подготовить данные заказов для записи в таблицу.

        Returns:
            Список кортежей следующей структуры:
            ``(first_name, last_name, title, birth_date, notes)``.
            Некорректные CSV-записи пропускаются методом ``load_from_csv``.
        """
        orders = cls.load_from_csv()
        return [
            (
                order.order_id,
                order.customer_id,
                order.employee_id,
                order.order_date,
                order.ship_city,
            )
            for order in orders
        ]


def main() -> None:
    """Подготовить строки и проверить подключение к базе данных."""
    employee_rows = NorthEmployee.from_rows()
    customer_rows = NorthCustomer.from_rows()
    order_rows = NorthOrder.from_rows()

    db_config = get_db_config()
    if db_config is None:
        return

    connection = connect_to_database(db_config)
    if connection is None:
        return

    logger = get_file_logger("main")

    try:
        with connection:
            employees_count = insert_employees(connection, employee_rows)
            customers_count = insert_customers(connection, customer_rows)
            orders_count = insert_orders(connection, order_rows)
    except (psycopg2.Error, UnicodeDecodeError) as error:
        message = f"Ошибка записи данных в базу: {error}"
        logger.error(message)
        print(message)
    else:
        message = (
            "Запись завершена: "
            f"employees — {employees_count}, "
            f"customers — {customers_count}, "
            f"orders — {orders_count}"
        )
        logger.info(message)
        print(message)
    finally:
        connection.close()
        logger.info("Соединение с базой данных закрыто")


if __name__ == "__main__":  # pragma: no cover
    main()
