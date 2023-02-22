from __future__ import annotations

from pathlib import Path

import loguru
import xarray as xr
from pyaerocom_preproc.check_obs import time_checker
from pyaerocom_preproc.error_db import read_errors


def test_time_checker(good_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=good_nc):
        time_checker(xr.open_dataset(good_nc))
    assert read_errors(good_nc, database=database) == []


def test_empty(empty_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=empty_nc):
        time_checker(xr.open_dataset(empty_nc))

    assert set(read_errors(empty_nc, database=database)) == {
        ("time_checker", "missing 'datetime_start' field"),
        ("time_checker", "missing 'datetime_stop' field"),
    }
