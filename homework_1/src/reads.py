"""Вспомогательные функции для загрузки данных из CSV, Excel и JSON."""

import csv
import json
from pathlib import Path
from typing import Any, cast
from zipfile import BadZipFile

import pandas as pd
from src.logging_config import get_file_logger

Transaction = dict[str, Any]

logger = get_file_logger("reads")


def get_transactions_from_csv(file_path: str | Path, delimiter: str = ";") -> list[Transaction]:
    """Загрузить список финансовых транзакций из CSV-файла.

    Пустые строки и строки, содержащие только пробелы или разделители,
    пропускаются.

    Args:
        file_path: Путь к CSV-файлу с транзакциями.

    Returns:
        Список словарей с транзакциями. Если файл отсутствует,
        недоступен, пуст или содержит некорректные данные,
        возвращается пустой список.
    """
    logger.debug("Начало загрузки транзакций из файла: %s", file_path)

    transactions: list[Transaction] = []

    try:
        with open(
            file_path,
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file, delimiter=delimiter)

            if reader.fieldnames is None:
                logger.error(
                    "Некорректная структура файла %s: отсутствует строка наименования столбцов.",
                    file_path,
                )
                return []

            skipped_items = 0
            for row in reader:
                row_is_empty = not any(isinstance(value, str) and value.strip() for value in row.values())

                if row_is_empty:
                    skipped_items += 1
                    continue

                transactions.append(cast(Transaction, dict(row)))

    except (OSError, UnicodeDecodeError, csv.Error) as error:
        logger.error(
            "Не удалось загрузить транзакции из файла %s: %s",
            file_path,
            error,
        )
        return []

    if skipped_items:
        logger.warning(
            "В файле %s пропущено некорректных элементов: %d",
            file_path,
            skipped_items,
        )

    logger.info(
        "Успешно загружено транзакций из файла %s: %d",
        file_path,
        len(transactions),
    )

    return transactions


def get_transactions_from_xls(file_path: str | Path) -> list[Transaction]:
    """Загрузить список финансовых транзакций из Excel файла.

    Пустые строки и строки, содержащие только пробелы или разделители,
    пропускаются.

    Args:
        file_path: Путь к Excel файлу с транзакциями.

    Returns:
        Список словарей с транзакциями. Если файл отсутствует,
        недоступен, пуст или содержит некорректные данные,
        возвращается пустой список.
    """
    logger.debug("Начало загрузки транзакций из файла: %s", file_path)

    try:
        data_frame = pd.read_excel(file_path, sheet_name="Отчет по операциям")

        if data_frame.empty:
            logger.info("Файл %s пуст.", file_path)
            return []

        records = cast(
            list[dict[str, Any]],
            data_frame.to_dict(orient="records"),
        )

        transactions: list[Transaction] = []
        skipped_items = 0

        for record in records:
            row_is_empty = not any(
                not pd.isna(value) and (not isinstance(value, str) or bool(value.strip())) for value in record.values()
            )

            if row_is_empty:
                skipped_items += 1
                continue

            transactions.append(cast(Transaction, record))

        if skipped_items:
            logger.warning(
                "В файле %s пропущено некорректных элементов: %d",
                file_path,
                skipped_items,
            )

        logger.info(
            "Успешно загружено транзакций из файла %s: %d",
            file_path,
            len(transactions),
        )

        return transactions

    except (
        OSError,
        ValueError,
        ImportError,
        BadZipFile,
    ) as error:
        logger.error(
            "Не удалось загрузить транзакции из файла %s: %s",
            file_path,
            error,
        )
        return []


def get_fields_from_json(file_path: str | Path) -> Any:
    """Загрузить данные из JSON-файла.

    Args:
        file_path: Путь к JSON-файлу.
    """
    logger.debug("Начало загрузки структур из файла: %s", file_path)

    try:
        with open(file_path, encoding="utf-8") as file:
            data: Any = json.load(file)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        logger.error(
            "Не удалось загрузить %s: %s",
            file_path,
            error,
        )
        return []

    if not isinstance(data, (dict, list)):
        logger.error(
            "Корневым элементом %s должен быть объект или массив",
            file_path,
        )
        return []

    logger.info(
        "Успешно загружено данных из файла %s: %d",
        file_path,
        len(data),
    )

    return data
