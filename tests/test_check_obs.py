from __future__ import annotations

from pathlib import Path

import loguru
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from pyaerocom_preproc.check_obs import (
    coord_checker,
    data_checker,
    infer_freq,
    monotonically_increasing,
    time_checker,
    years,
)
from pyaerocom_preproc.error_db import read_errors


@pytest.fixture(params=(2020, 2022))
def year(request) -> int:
    return request.param


@pytest.fixture(params=("1D", "1H"))
def freq(request) -> str:
    return request.param


@pytest.fixture
def datetime_start(year: int, freq: str) -> xr.DataArray:
    data = pd.date_range(f"{year}-01-01 00:00", f"{year}-12-31 23:00", freq=freq)
    da = xr.DataArray(data, dims="time", name="datetime_start")
    return da.reset_coords().drop_vars("time")["datetime_start"]


@pytest.fixture
def datetime_stop(year: int, freq: str) -> xr.DataArray:
    start = {"1H": f"{year}-01-01 01:00", "1D": f"{year}-01-02 00:00"}
    data = pd.date_range(start[freq], f"{year+1}-01-01 00:00", freq=freq)
    da = xr.DataArray(data, dims="time", name="datetime_stop")
    return da.reset_coords().drop_vars("time")["datetime_stop"]


@pytest.fixture
def patched_logger(logger: loguru.Logger, monkeypatch) -> loguru.Logger:
    monkeypatch.setattr("pyaerocom_preproc.check_obs.logger", logger)
    return logger


def test_monotonically_increasing(datetime_start: xr.DataArray, datetime_stop: xr.DataArray):
    for time in (datetime_start, datetime_stop):
        assert monotonically_increasing(time)
        assert not monotonically_increasing(time.roll({"time": 1}))


def test_infer_freq(datetime_start: xr.DataArray, datetime_stop: xr.DataArray, freq: str):
    assert infer_freq(datetime_start.diff("time")) == freq
    assert infer_freq(datetime_stop.diff("time")) == freq
    assert infer_freq(datetime_stop - datetime_start) == freq


def test_infer_years(datetime_start: xr.DataArray, datetime_stop: xr.DataArray, year: int):
    assert years(datetime_start) == {year}
    assert years(datetime_stop) == {year, year + 1}


@pytest.fixture
def good_nc(tmp_path: Path, datetime_start: xr.DataArray, datetime_stop: xr.DataArray) -> Path:
    path = tmp_path / "good.nc"

    def dummy(**attrs):
        return xr.DataArray(
            np.full_like(datetime_start, None, dtype=float), dims="time", attrs=attrs
        )

    data = dict(
        datetime_start=datetime_start,
        datetime_stop=datetime_stop,
        latitude=xr.DataArray(0, attrs=dict(units="degree_north")),
        longitude=xr.DataArray(0, attrs=dict(units="degree_east")),
        altitude=xr.DataArray(0, attrs=dict(units="m")),
        air_quality_index=dummy(units="1"),
        CO_density=dummy(units="mg/m3"),
        NO2_density=dummy(units="ug/m3"),
        O3_density=dummy(units="ug/m3"),
        PM10_density=dummy(units="ug/m3"),
        PM2p5_density=dummy(units="ug/m3"),
        SO2_density=dummy(units="ug/m3"),
    )
    xr.Dataset(data).to_netcdf(
        path,
        encoding={
            var: dict(_FillValue=None) for var in data if var.endswith(("_index", "_density"))
        },
    )
    return path


@pytest.fixture(scope="module")
def empty_nc(tmp_path_factory) -> Path:
    path: Path = tmp_path_factory.mktemp("data") / "empty.nc"
    xr.Dataset().to_netcdf(path)
    return path


def test_time_checker(good_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=good_nc):
        time_checker(xr.open_dataset(good_nc))
    assert read_errors(good_nc, database=database) == []


def test_time_checker_empty(empty_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=empty_nc):
        time_checker(xr.open_dataset(empty_nc))

    assert set(read_errors(empty_nc, database=database)) == {
        ("time_checker", "missing 'time' field"),
        ("time_checker", "missing 'datetime_start' field"),
        ("time_checker", "missing 'datetime_stop' field"),
    }


@pytest.mark.parametrize("year,freq", ((2022, "1D"),))
def test_coord_checker(good_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=good_nc):
        coord_checker(xr.open_dataset(good_nc))
    assert read_errors(good_nc, database=database) == []


def test_coord_checker_empty(empty_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=empty_nc):
        coord_checker(xr.open_dataset(empty_nc))

    assert set(read_errors(empty_nc, database=database)) == {
        ("coord_checker", "missing 'latitude' field"),
        ("coord_checker", "missing 'longitude' field"),
        ("coord_checker", "missing 'altitude' field"),
    }


@pytest.mark.parametrize("year,freq", ((2022, "1D"),))
def test_data_checker(good_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=good_nc):
        data_checker(xr.open_dataset(good_nc))

    assert read_errors(good_nc, database=database) == []


def test_data_checker_empty(empty_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=empty_nc):
        data_checker(xr.open_dataset(empty_nc))

    assert set(read_errors(empty_nc, database=database)) == {
        ("data_checker", "missing 'time' field"),
    }
