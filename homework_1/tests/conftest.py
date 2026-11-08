"""Настройка путей импорта для тестов домашнего задания."""

import sys
from pathlib import Path

HOMEWORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOMEWORK_DIR))
