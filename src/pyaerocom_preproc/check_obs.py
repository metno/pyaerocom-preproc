from __future__ import annotations

from typing import Literal

import numpy as np
import xarray as xr
from loguru import logger


def time_checker(ds: xr.Dataset) -> None:
    if (time := ds.get("time")) is None:
        logger.error("missing 'time' field")
    if (datetime_start := ds.get("datetime_start")) is None:
        logger.error("missing 'datetime_start' field")
    if (datetime_stop := ds.get("datetime_stop")) is None:
        logger.error("missing 'datetime_stop' field")

    if time is None or datetime_start is None or datetime_stop is None:
        return

    if datetime_start.size != time.size:
        logger.error(f"{datetime_start.size=} != {time.size=}")
    if datetime_stop.size != time.size:
        logger.error(f"{datetime_stop.size=} != {time.size=}")

    if not (datetime_start.size == datetime_stop.size == time.size):
        return

    if not monotonically_increasing(datetime_start):
        logger.error("datetime_start is not monotonically increasing")
    if not monotonically_increasing(datetime_stop):
        logger.error("datetime_stop is not monotonically increasing")
    if not (datetime_start <= datetime_stop).all():
        logger.error("datetime_start <!= datetime_stop")
        return

    if (freq := infer_freq(datetime_stop - datetime_start)) == "?":
        logger.error(f"not hourly or daily frequency")

    if len(years(datetime_start)) > 1:
        logger.error("different years")

    days = 366 if datetime_start.dt.is_leap_year.any() else 365
    records = {"1D": days, "1H": days * 24}
    if freq in records and time.size < records[freq]:
        logger.error("not a full year")


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
