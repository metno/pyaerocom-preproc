from __future__ import annotations

from pathlib import Path

import loguru
from pyaerocom_preproc.error_db import read_errors


def test_read_errors(path: Path, logger: loguru.Logger, database: Path):
    assert not read_errors(path, database=database)

    def error_report():
        logger.error("error_report")

    with logger.contextualize(path=path):
        # ignored
        logger.debug("debug")
        logger.success("success")
        logger.critical("critical")
        logger.error("error, skip")
        error_report()
        # logged into db
        logger.error("error 1")
        logger.error("error 2")
        logger.error("error 3")
        # repeated
        logger.error("error 3")
        logger.error("error 2")
        logger.error("error 1")

    assert read_errors(path, database=database) == [
        ("test_read_errors", "error 1"),
        ("test_read_errors", "error 2"),
        ("test_read_errors", "error 3"),
    ]
