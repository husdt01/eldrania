"""Работа с SQLite: соединения и транзакции.

Каждая операция выполняется в транзакции BEGIN IMMEDIATE: SQLite сериализует записи,
поэтому проверки баланса и выдача наград атомарны, а гонки двух запросов невозможны.
"""
import sqlite3
from contextlib import contextmanager

import config
from models import SCHEMA


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, timeout=15, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.DatabaseError:
        pass
    return conn


def init_db() -> None:
    conn = connect()
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


@contextmanager
def transaction():
    """Открывает соединение и транзакцию; коммит при успехе, откат при любой ошибке."""
    conn = connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        conn.close()
