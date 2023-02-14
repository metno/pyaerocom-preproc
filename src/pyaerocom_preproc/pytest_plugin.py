from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Iterator, Literal

import numpy as np
import pytest
import xarray as xr


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--pya-pp-obs",
        nargs="?",
        action="store",
        default=None,
        const=".*.nc",
        help="obs dataset regex",
    )


def pytest_collect_file(parent: pytest.Collector, file_path: Path):
    pya_pp = parent.config.getoption("--pya-pp-obs")
    if pya_pp is not None and re.match(pya_pp, file_path.name):
        return ObsFile.from_parent(parent, path=file_path)


class ObsFile(pytest.File):
    def collect(self):
        yield CheckFile.from_parent(
            self.parent, name="file_exists", check_func=check_file_exists, path=self.path
        )
        yield CheckFile.from_parent(
            self.parent, name="time_vars", check_func=check_time, path=self.path
        )


class CheckFile(pytest.Item):
    def __init__(self, *, check_func: Callable[[Path], None], **kwargs):
        super().__init__(**kwargs)
        self.check_func = check_func

    def runtest(self):
        self.check_func(self.path)

    def reportinfo(self):
        return self.path, None, self.name


def check_file_exists(path: Path):
    assert path.exists(), f"missing {path.name}"
    assert path.is_file(), f"{path.name} is not a file"


def check_time(path: Path):
    ds = xr.open_dataset(path)
    errors = list(time_checker(ds))
    assert not errors, ", ".join(errors)


def time_checker(ds: xr.Dataset) -> Iterator[str]:
    if (time := ds.get("time", None)) is None:
        yield "missing 'time' field"
    if (datetime_start := ds.get("datetime_start", None)) is None:
        yield "missing 'datetime_start' field"
    if (datetime_stop := ds.get("datetime_stop", None)) is None:
        yield "missing 'datetime_stop' field"

    if datetime_start.size != time.size:
        yield f"{datetime_start.size=} != {time.size=}"
    if datetime_stop.size != time.size:
        yield f"{datetime_stop.size=} != {time.size=}"

    if not monotonically_increasing(datetime_start):
        yield "datetime_start is not monotonically increasing"
    if not monotonically_increasing(datetime_stop):
        yield "datetime_stop is not monotonically increasing"
    if not (datetime_start <= datetime_stop).all():
        yield "datetime_start <!= datetime_stop"

    if (freq := infer_freq(datetime_stop - datetime_start)) == "?":
        yield f"not hourly or daily frequency"

    if len(years(datetime_start)) > 1:
        yield "different years"

    days = 366 if datetime_start.dt.is_leap_year.any() else 365
    records = {"1D": days, "1H": days * 24}
    if freq in records and time.size < records[freq]:
        yield "not a full year"


def monotonically_increasing(time: xr.DataArray) -> bool:
    return (time.diff("time").data.view(int) > 0).all()


def infer_freq(time_delta: xr.DataArray) -> Literal["1H", "1D", "?"]:
    if np.unique(time_delta.dt.seconds) == [3600]:
        return "1H"
    if np.unique(time_delta.dt.days) == [1]:
        return "1D"
    return "?"


def years(time: xr.DataArray) -> set[int]:
    return set(np.unique(time.dt.year))
