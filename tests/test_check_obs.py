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


@pytest.mark.parametrize("year", (2020, 2022))
@pytest.mark.parametrize("freq", ("1D", "1H"))
def test_monotonically_increasing(datetime_start: xr.DataArray, datetime_stop: xr.DataArray):
    for time in (datetime_start, datetime_stop):
        assert monotonically_increasing(time)
        assert not monotonically_increasing(time.roll({"time": 1}))


@pytest.mark.parametrize("year", (2020, 2022))
@pytest.mark.parametrize("freq", ("1D", "1H"))
def test_infer_freq(datetime_start: xr.DataArray, datetime_stop: xr.DataArray, freq: str):
    assert infer_freq(datetime_start.diff("time")) == freq
    assert infer_freq(datetime_stop.diff("time")) == freq
    assert infer_freq(datetime_stop - datetime_start) == freq


@pytest.mark.parametrize("year", (2020, 2022))
@pytest.mark.parametrize("freq", ("1D", "1H"))
def test_infer_years(datetime_start: xr.DataArray, datetime_stop: xr.DataArray, year: int):
    assert years(datetime_start) == {year}
    assert years(datetime_stop) == {year, year + 1}


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


@pytest.fixture
def wrong_coords_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    def dummy(value, **attrs):
        return xr.DataArray(
            np.full_like(good_ds["time"], value, dtype=float), dims="time", attrs=attrs
        )

    path = tmp_path / "wrong_coords.nc"
    data = dict(
        latitude=dummy(-100, units="degN"),  # wrong unit
        longitude=dummy(360, units="degE"),  # wrong unit
        altitude=dummy(0),  # missing unit
    )
    xr.Dataset(data).to_netcdf(path)
    return path


@pytest.fixture
def wrong_dims_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    path = tmp_path / "wrong_dims.nc"
    ds = good_ds.expand_dims(dict(latitude=1, longitude=1))[["air_quality_index"]]
    ds.to_netcdf(
        path,
        encoding={"air_quality_index": dict(_FillValue=None)},
    )
    return path


@pytest.fixture
def wrong_units_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    path = tmp_path / "wrong_units.nc"
    del good_ds["air_quality_index"].attrs["units"]  # missing unit
    good_ds["CO_density"].attrs["units"] = "ug/m3"  # wrong unit
    good_ds.to_netcdf(
        path,
        encoding={
            var: dict(_FillValue=None)
            for var in good_ds.data_vars
            if var.endswith(("_index", "_density"))
        },
    )
    return path


@pytest.fixture
def negative_nc(tmp_path: Path, good_ds: xr.Dataset) -> Path:
    path = tmp_path / "negative.nc"
    vars = dict(
        CO_density=-1,
        NO2_density=-1,
        O3_density=-1,
        PM10_density=-1,
        PM2p5_density=-1,
        SO2_density=-1,
    )
    xr.full_like(good_ds.drop_vars("air_quality_index"), vars).to_netcdf(
        path,
        encoding={var: dict(_FillValue=None) for var in vars},
    )
    return path


def test_time_checker(good_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=good_nc):
        time_checker(xr.open_dataset(good_nc))
    assert read_errors(good_nc, database=database) == []


def test_time_checker_empty(empty_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=empty_nc):
        time_checker(xr.open_dataset(empty_nc))

    assert set(read_errors(empty_nc, database=database)) == {
        ("time_checker", "missing 'datetime_start' field"),
        ("time_checker", "missing 'datetime_stop' field"),
    }


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


def test_coord_checker_wrong_coords(
    wrong_coords_nc: Path, patched_logger: loguru.Logger, database: Path
):
    with patched_logger.contextualize(path=wrong_coords_nc):
        coord_checker(xr.open_dataset(wrong_coords_nc))

    assert set(read_errors(wrong_coords_nc, database=database)) == {
        ("coord_checker", "latitude.size=366 != 1"),
        ("coord_checker", "longitude.size=366 != 1"),
        ("coord_checker", "altitude.size=366 != 1"),
        ("coord_checker", "missing altitude.units"),
        ("coord_checker", "latitude.units='degN' != 'degree_north'"),
        ("coord_checker", "longitude.units='degE' != 'degree_east'"),
        ("coord_checker", "latitude out of range [-90, 90]"),
        ("coord_checker", "longitude out of range [-180, 180]"),
    }


def test_data_checker(good_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=good_nc):
        data_checker(xr.open_dataset(good_nc))

    assert read_errors(good_nc, database=database) == []


def test_data_checker_empty(empty_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=empty_nc):
        data_checker(xr.open_dataset(empty_nc))

    assert set(read_errors(empty_nc, database=database)) == {
        ("data_checker", "missing obs found"),
    }


def test_data_checker_wrong_dims(
    wrong_dims_nc: Path, patched_logger: loguru.Logger, database: Path
):
    with patched_logger.contextualize(path=wrong_dims_nc):
        data_checker(xr.open_dataset(wrong_dims_nc))

    assert set(read_errors(wrong_dims_nc, database=database)) == {
        ("data_checker", "air_quality_index.dims=('latitude', 'longitude', 'time') != ('time',)"),
    }


def test_data_checker_wrong_units(
    wrong_units_nc: Path, patched_logger: loguru.Logger, database: Path
):
    with patched_logger.contextualize(path=wrong_units_nc):
        data_checker(xr.open_dataset(wrong_units_nc))

    assert set(read_errors(wrong_units_nc, database=database)) == {
        ("data_checker", "missing air_quality_index.units"),
        ("data_checker", "CO_density.units='ug/m3' not in ['mg m-3', 'mg/m3']"),
    }


def test_data_checker_negative_values(
    negative_nc: Path, patched_logger: loguru.Logger, database: Path
):
    with patched_logger.contextualize(path=negative_nc):
        data_checker(xr.open_dataset(negative_nc))

    assert set(read_errors(negative_nc, database=database)) == {
        ("data_checker", "CO_density has negative values"),
        ("data_checker", "NO2_density has negative values"),
        ("data_checker", "O3_density has negative values"),
        ("data_checker", "PM10_density has negative values"),
        ("data_checker", "PM2p5_density has negative values"),
        ("data_checker", "SO2_density has negative values"),
    }
