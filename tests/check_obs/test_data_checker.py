from __future__ import annotations

from pathlib import Path

import loguru
import pytest
import xarray as xr
from pyaerocom_preproc.check_obs import data_checker
from pyaerocom_preproc.error_db import read_errors


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


def test_data_checker(good_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=good_nc):
        data_checker(xr.open_dataset(good_nc))

    assert read_errors(good_nc, database=database) == []


def test_empty(empty_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=empty_nc):
        data_checker(xr.open_dataset(empty_nc))

    assert set(read_errors(empty_nc, database=database)) == {
        ("data_checker", "missing obs found"),
    }


def test_wrong_dims(wrong_dims_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=wrong_dims_nc):
        data_checker(xr.open_dataset(wrong_dims_nc))

    assert set(read_errors(wrong_dims_nc, database=database)) == {
        ("data_checker", "air_quality_index.dims=('latitude', 'longitude', 'time') != ('time',)"),
    }


def test_wrong_units(wrong_units_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=wrong_units_nc):
        data_checker(xr.open_dataset(wrong_units_nc))

    assert set(read_errors(wrong_units_nc, database=database)) == {
        ("data_checker", "missing air_quality_index.units"),
        ("data_checker", "CO_density.units='ug/m3' not in ['mg m-3', 'mg/m3']"),
    }


def test_negative_values(negative_nc: Path, patched_logger: loguru.Logger, database: Path):
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
