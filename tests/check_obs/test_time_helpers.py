from __future__ import annotations

import pytest
import xarray as xr
from pyaerocom_preproc.check_obs import infer_freq, monotonically_increasing, years


@pytest.fixture(params=(2020, 2022))
def year(request) -> int:
    return request.param


@pytest.fixture(params=("1D", "1H"))
def freq(request) -> str:
    return request.param


def test_monotonically_increasing(datetime_start: xr.DataArray, datetime_stop: xr.DataArray):
    for time in (datetime_start, datetime_stop):
        assert monotonically_increasing(time)
        assert not monotonically_increasing(time.roll({"time": 1}))


def test_infer_freq(datetime_start: xr.DataArray, datetime_stop: xr.DataArray, freq: str):
    assert infer_freq(datetime_start.diff("time")) == freq
    assert infer_freq(datetime_stop.diff("time")) == freq
    assert infer_freq(datetime_stop - datetime_start) == freq


def test_years(datetime_start: xr.DataArray, datetime_stop: xr.DataArray, year: int):
    assert years(datetime_start) == {year}
    assert years(datetime_stop) == {year, year + 1}
