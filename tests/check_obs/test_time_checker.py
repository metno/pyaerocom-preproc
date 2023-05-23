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


def test_wrong_dims(wrong_dims_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=wrong_dims_nc):
        time_checker(xr.open_dataset(wrong_dims_nc))

    assert set(read_errors(wrong_dims_nc, database=database)) == {
        ("time_checker", "datetime_start.dims=('latitude', 'longitude', 'time') != ('time',)"),
        ("time_checker", "datetime_stop.dims=('latitude', 'longitude', 'time') != ('time',)"),
    }


def test_bad_times(bad_times_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=bad_times_nc):
        time_checker(xr.open_dataset(bad_times_nc))

    assert set(read_errors(bad_times_nc, database=database)) == {
        ("time_checker", "datetime_start is not monotonically increasing"),
        ("time_checker", "datetime_stop is not monotonically increasing"),
        ("time_checker", "datetime_start <!= datetime_stop"),
    }


def test_wrong_years(wrong_years_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=wrong_years_nc):
        time_checker(xr.open_dataset(wrong_years_nc))

    assert set(read_errors(wrong_years_nc, database=database)) == {
        ("time_checker", "not hourly or daily frequency"),
        ("time_checker", "different years"),
    }


def test_incomplete(incomplete_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=incomplete_nc):
        time_checker(xr.open_dataset(incomplete_nc))

    assert set(read_errors(incomplete_nc, database=database)) == {
        ("time_checker", "not a full year"),
    }


def test_icos_co2_nrt(icos_co2_nrt: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=icos_co2_nrt):
        time_checker(xr.open_dataset(icos_co2_nrt))

    assert set(read_errors(icos_co2_nrt, database=database)) == {
        ("time_checker", "not a full year"),
    }
