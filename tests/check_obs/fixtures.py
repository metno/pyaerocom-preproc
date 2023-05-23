from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

if sys.version_info >= (3, 11):  # pragma: no cover
    from importlib import resources
else:  # pragma: no cover
    import importlib_resources as resources

import loguru
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
def empty_nc() -> Iterator[Path]:
    resource = resources.files(__package__) / "empty.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def good_nc(year: int, freq: str) -> Iterator[Path]:
    resource = resources.files(__package__) / f"valid-{freq}-{year}.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def wrong_coords_nc(year: int, freq: str) -> Iterator[Path]:
    resource = resources.files(__package__) / f"wrong_coords-{freq}-{year}.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def wrong_dims_nc(year: int, freq: str) -> Iterator[Path]:
    resource = resources.files(__package__) / f"wrong_dims-{freq}-{year}.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def wrong_units_nc(year: int, freq: str) -> Iterator[Path]:
    resource = resources.files(__package__) / f"wrong_units-{freq}-{year}.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def negative_nc(year: int, freq: str) -> Iterator[Path]:
    resource = resources.files(__package__) / f"negative_density-{freq}-{year}.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def bad_times_nc(year: int, freq: str) -> Iterator[Path]:
    resource = resources.files(__package__) / f"bad_times-{freq}-{year}.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def wrong_years_nc(year: int, freq: str) -> Iterator[Path]:
    resource = resources.files(__package__) / f"wrong_years-{freq}-{year}.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def incomplete_nc(year: int, freq: str) -> Iterator[Path]:
    resource = resources.files(__package__) / f"incomplete-{freq}-{year}.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path


@pytest.fixture
def icos_co2_nrt() -> Iterator[Path]:
    resource = resources.files(__package__) / f"icos-co2-nrt-bir-10.0m-20230401-20230403T100446.nc"
    assert resource.is_file()
    with resources.as_file(resource) as path:
        yield path
