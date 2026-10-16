"""Конфигурация из переменных окружения (и файла .env, если установлен python-dotenv)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:  # python-dotenv необязателен
    pass


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").strip().lower() in ("1", "true", "yes", "on")


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DEV_MODE = _flag("DEV_MODE")
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "game.db"))
INITDATA_MAX_AGE = int(os.getenv("INITDATA_MAX_AGE", "86400"))  # секунд
IDLE_CAP_HOURS = float(os.getenv("IDLE_CAP_HOURS", "12"))
# Платежи в MVP отключены. Флаг зарезервирован для будущей интеграции Telegram Stars.
PAYMENTS_ENABLED = False
