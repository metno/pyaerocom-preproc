from __future__ import annotations

from pathlib import Path

import loguru
import xarray as xr
from pyaerocom_preproc.check_obs import data_checker
from pyaerocom_preproc.error_db import read_errors


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
        ("data_checker", "CO_density.dims=('latitude', 'longitude', 'time') != ('time',)"),
        ("data_checker", "NO2_density.dims=('latitude', 'longitude', 'time') != ('time',)"),
        ("data_checker", "O3_density.dims=('latitude', 'longitude', 'time') != ('time',)"),
        ("data_checker", "PM10_density.dims=('latitude', 'longitude', 'time') != ('time',)"),
        ("data_checker", "PM2p5_density.dims=('latitude', 'longitude', 'time') != ('time',)"),
        ("data_checker", "SO2_density.dims=('latitude', 'longitude', 'time') != ('time',)"),
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
