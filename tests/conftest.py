from __future__ import annotations

from pathlib import Path

import loguru
import pytest
from loguru import logger as _logger
from pyaerocom_preproc.error_db import logging_patcher


@pytest.fixture(params=("check1", "hash2", "test3"))
def text(request) -> str:
    return request.param


@pytest.fixture
def path(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "check.txt"
    path.write_text(text)
    return path


@pytest.fixture
def database(tmp_path: Path) -> Path:
    return tmp_path / "errors.sqlite"


@pytest.fixture
def logger(database: Path) -> loguru.Logger:
    return _logger.patch(logging_patcher(database))
