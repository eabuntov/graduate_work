import logging

import psycopg2
from psycopg2 import OperationalError, InterfaceError
from psycopg2.extras import DictCursor
from contextlib import contextmanager
from typing import Generator, Any, Dict
import backoff


@backoff.on_exception(
    backoff.expo,
    (OperationalError, InterfaceError),
    max_tries=5,
    jitter=None,
)
def connect_with_retry(dsn: Dict[str, Any]):
    """Подключение к БД с backoff, 5 попыток подключения"""
    return psycopg2.connect(**dsn, cursor_factory=DictCursor)


@contextmanager
def get_db_cursor(
    dsn: Dict[str, Any],
) -> Generator[psycopg2.extensions.cursor, None, None]:
    """
    Контекстный менеджер, обеспечивающий подключение к БД
    Использует backoff для обработки сетевых ошибок.
    :param dsn: Словарь с настройками подключения
    """
    conn = connect_with_retry(dsn)
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


@backoff.on_exception(
    backoff.expo,
    (OperationalError, InterfaceError),
    max_tries=None,  # Retry forever
    jitter=backoff.full_jitter,
    on_backoff=lambda details: logging.warning(
        f"Reconnecting to Postgres (attempt {details['tries']})..."
    ),
)
def connect_and_listen(
    dsn: Dict[str, Any], channel: str
) -> tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
    """Подключение к БД и установка триггеров для слежения за изменениями.
    :param dsn: Словарь с настройками подключения
    """
    conn = psycopg2.connect(**dsn, cursor_factory=DictCursor)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    with open("sql/triggers.sql", "r", encoding="utf-8") as query_file:
        cur.execute(query_file.read())
    conn.commit()
    cur.execute(f"LISTEN {channel};")
    logging.info(f"Connected and listening on channel '{channel}'")
    return conn, cur
