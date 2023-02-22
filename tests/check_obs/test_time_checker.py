from __future__ import annotations

from pathlib import Path

import loguru
import pytest
import xarray as xr
from pyaerocom_preproc.check_obs import time_checker
from pyaerocom_preproc.error_db import read_errors


@pytest.fixture
def wrong_dims_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    path = tmp_path / "wrong_dims.nc"
    good_ds.expand_dims(dict(latitude=1, longitude=1)).to_netcdf(path)
    return path


@pytest.fixture
def bad_times_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    path = tmp_path / "bad_times.nc"
    good_ds.assign(
        datetime_start=good_ds["datetime_start"].roll(time=7),
        datetime_stop=good_ds["datetime_stop"].roll(time=-7),
    ).to_netcdf(path)
    return path


@pytest.fixture
def wrong_years_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    path = tmp_path / "wrong_years.nc"
    good_ds.assign(datetime_start=good_ds["datetime_stop"]).to_netcdf(path)
    return path


@pytest.fixture
def incomplete_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    path = tmp_path / "incomplete.nc"
    good_ds.isel(time=slice(None, None, 2)).to_netcdf(path)
    return path


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
