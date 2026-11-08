"""Тесты функций чтения данных из файлов."""

import csv
from pathlib import Path
from unittest.mock import Mock
from zipfile import BadZipFile

import pandas as pd
import pytest
from src import reads


def test_get_transactions_from_csv_reads_rows_with_custom_delimiter(tmp_path: Path) -> None:
    """CSV-файл читается с переданным разделителем и BOM."""
    csv_file = tmp_path / "transactions.csv"
    csv_file.write_text("id,description\n1,Payment\n2,Transfer\n", encoding="utf-8-sig")

    assert reads.get_transactions_from_csv(csv_file, delimiter=",") == [
        {"id": "1", "description": "Payment"},
        {"id": "2", "description": "Transfer"},
    ]


def test_get_transactions_from_csv_skips_empty_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Пустые CSV-строки пропускаются и логируются."""
    csv_file = tmp_path / "transactions.csv"
    csv_file.write_text("id;description\n;\n1;Payment\n   ; \n", encoding="utf-8")
    warning_mock = Mock()
    monkeypatch.setattr(reads.logger, "warning", warning_mock)

    assert reads.get_transactions_from_csv(csv_file) == [{"id": "1", "description": "Payment"}]
    warning_mock.assert_called_once()


def test_get_transactions_from_csv_returns_empty_list_for_empty_file(tmp_path: Path) -> None:
    """CSV без заголовка возвращает пустой список."""
    csv_file = tmp_path / "empty.csv"
    csv_file.touch()

    assert reads.get_transactions_from_csv(csv_file) == []


@pytest.mark.parametrize("content", [b"\xff\xfe\x00", b"id;description\n1;Payment\n"])
def test_get_transactions_from_csv_returns_empty_list_on_read_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    content: bytes,
) -> None:
    """Ошибки кодировки и CSV преобразуются в пустой список."""
    csv_file = tmp_path / "broken.csv"
    csv_file.write_bytes(content)

    if content.startswith(b"id"):
        monkeypatch.setattr(reads.csv, "DictReader", Mock(side_effect=csv.Error("broken CSV")))

    assert reads.get_transactions_from_csv(csv_file) == []


def test_get_transactions_from_csv_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    """Отсутствующий CSV-файл возвращает пустой список."""
    assert reads.get_transactions_from_csv(tmp_path / "missing.csv") == []


def test_get_transactions_from_xls_reads_records(monkeypatch: pytest.MonkeyPatch) -> None:
    """Лист Excel преобразуется в список словарей."""
    excel_file = Path("transactions.xlsx")
    data_frame = pd.DataFrame(
        [
            {"id": 1, "description": "Payment"},
            {"id": 2, "description": "Transfer"},
        ]
    )
    read_excel_mock = Mock(return_value=data_frame)
    monkeypatch.setattr(reads.pd, "read_excel", read_excel_mock)

    assert reads.get_transactions_from_xls(excel_file) == [
        {"id": 1, "description": "Payment"},
        {"id": 2, "description": "Transfer"},
    ]
    read_excel_mock.assert_called_once_with(excel_file, sheet_name="Отчет по операциям")


def test_get_transactions_from_xls_skips_empty_records(monkeypatch: pytest.MonkeyPatch) -> None:
    """Пустые строки Excel пропускаются."""
    data_frame = pd.DataFrame(
        [
            {"id": None, "description": " "},
            {"id": 1, "description": "Payment"},
            {"id": float("nan"), "description": None},
        ]
    )
    monkeypatch.setattr(reads.pd, "read_excel", Mock(return_value=data_frame))
    warning_mock = Mock()
    monkeypatch.setattr(reads.logger, "warning", warning_mock)

    assert reads.get_transactions_from_xls("transactions.xlsx") == [{"id": 1.0, "description": "Payment"}]
    warning_mock.assert_called_once()


def test_get_transactions_from_xls_returns_empty_list_for_empty_sheet(monkeypatch: pytest.MonkeyPatch) -> None:
    """Пустой лист Excel возвращает пустой список."""
    monkeypatch.setattr(reads.pd, "read_excel", Mock(return_value=pd.DataFrame()))

    assert reads.get_transactions_from_xls("transactions.xlsx") == []


@pytest.mark.parametrize("error", [OSError("read error"), ValueError("bad sheet"), ImportError(), BadZipFile()])
def test_get_transactions_from_xls_returns_empty_list_on_read_error(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
) -> None:
    """Ожидаемые ошибки Excel возвращают пустой список."""
    monkeypatch.setattr(reads.pd, "read_excel", Mock(side_effect=error))

    assert reads.get_transactions_from_xls("transactions.xlsx") == []


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('{"currency": "RUB"}', {"currency": "RUB"}),
        ('[{"currency": "USD"}]', [{"currency": "USD"}]),
    ],
)
def test_get_fields_from_json_reads_object_or_array(tmp_path: Path, content: str, expected: object) -> None:
    """JSON-объект и массив возвращаются без изменений."""
    json_file = tmp_path / "fields.json"
    json_file.write_text(content, encoding="utf-8")

    assert reads.get_fields_from_json(json_file) == expected


@pytest.mark.parametrize("content", ["42", '"RUB"', "null"])
def test_get_fields_from_json_rejects_scalar_root(tmp_path: Path, content: str) -> None:
    """Скалярный корень JSON отклоняется."""
    json_file = tmp_path / "fields.json"
    json_file.write_text(content, encoding="utf-8")

    assert reads.get_fields_from_json(json_file) == []


@pytest.mark.parametrize("content", [b"{broken json", b"\xff\xfe\x00"])
def test_get_fields_from_json_returns_empty_list_for_invalid_content(tmp_path: Path, content: bytes) -> None:
    """Ошибки синтаксиса и кодировки JSON возвращают пустой список."""
    json_file = tmp_path / "broken.json"
    json_file.write_bytes(content)

    assert reads.get_fields_from_json(json_file) == []


def test_get_fields_from_json_returns_empty_list_for_missing_file(tmp_path: Path) -> None:
    """Отсутствующий JSON-файл возвращает пустой список."""
    assert reads.get_fields_from_json(tmp_path / "missing.json") == []
