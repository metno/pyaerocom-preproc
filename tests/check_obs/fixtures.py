from __future__ import annotations

from pathlib import Path

import loguru
import numpy as np
import pandas as pd
import pytest
import xarray as xr


@pytest.fixture(params=(2020,))
def year(request) -> int:
    return request.param


@pytest.fixture(params=("1D",))
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


@pytest.fixture
def good_ds(datetime_start: xr.DataArray, datetime_stop: xr.DataArray) -> xr.Dataset:
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
    return xr.Dataset(data)


@pytest.fixture
def good_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    path = tmp_path / "good.nc"
    good_ds.to_netcdf(
        path,
        encoding={
            var: dict(_FillValue=None)
            for var in good_ds.data_vars
            if var.endswith(("_index", "_density"))
        },
    )
    return path


@pytest.fixture(scope="module")
def empty_nc(tmp_path_factory) -> Path:
    path: Path = tmp_path_factory.mktemp("data") / "empty.nc"
    xr.Dataset().to_netcdf(path)
    return path
