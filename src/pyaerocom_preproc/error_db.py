from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Iterator

import loguru

__all__ = ["logging_patcher", "read_errors"]

DB_PATH = Path(f"~/.cache/{__package__}/errors.sqlite").expanduser()


@contextmanager
def connect(database: Path) -> Iterator[sqlite3.Connection]:
    try:
        db = sqlite3.connect(database)
        yield db
    except sqlite3.Error as e:
        exit(str(e))
    finally:
        db.close()


@contextmanager
def errors_db(database: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """
    create db and errors table, if do not exists already
    and yields a DB connection from within a context manager
    """
    if not database.exists():
        database.parent.mkdir(parents=True, exist_ok=True)
        create_table = """
            CREATE TABLE IF NOT EXISTS errors (
                file_name TEXT NOT NULL,
                test_func TEXT NOT NULL,
                error_msg TEXT NOT NULL,
                UNIQUE(file_name, test_func, error_msg)
            );
            """
        with connect(database) as db, closing(db.cursor()) as cur:
            cur.executescript(create_table)

    with connect(database) as db:
        yield db


def logging_patcher(database: Path = DB_PATH) -> loguru.PatcherFunction:
    """extract error info from records and write to DB"""
    insert = """
        INSERT or IGNORE INTO errors (file_name, test_func, error_msg)
        VALUES (?, ?, ?);
        """

    def patcher(record: loguru.Record) -> None:
        if record["level"].name != "ERROR":
            return
        with errors_db(database) as db, db, closing(db.cursor()) as cur:
            cur.execute(
                insert, (record["extra"]["path"].name, record["function"], record["message"])
            )

    return patcher


def read_errors(path: Path, *, database: Path = DB_PATH) -> list[tuple[str, str]]:
    """read messages from DB and return decoded observations"""

    select = """
        SELECT
            test_func, error_msg
        FROM
            errors 
        WHERE
            file_name IS ?;
        """
    with errors_db(database) as db, closing(db.cursor()) as cur:
        cur.execute(select, (path.name,))
        return cur.fetchall()
