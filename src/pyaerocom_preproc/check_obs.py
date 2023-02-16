from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, List, Literal

import numpy as np
import xarray as xr
from loguru import logger

from .error_db import read_errors

__all__ = ["obs_checker"]

VARIABLE_UNITS = dict(
    air_quality_index="1",
    CO_density="mg/m3",
    NO2_density="ug/m3",
    O3_density="ug/m3",
    PM10_density="ug/m3",
    PM2p5_density="ug/m3",
    SO2_density="ug/m3",
)


REGISTERED_CHECKERS: list[Callable[[xr.Dataset], None]] = []


def register(func):
    REGISTERED_CHECKERS.append(func)
    return func


def obs_checker(data_set: str, files: List[Path]) -> None:
    """Check requirements for observations datasets"""
    regex = re.compile(rf"{data_set}.*.nc")
    for path in files:
        with logger.contextualize(path=path):
            if not regex.match(path.name):
                logger.error(f"filename does not match r'{regex.pattern}'")
                continue

            ds = xr.open_dataset(path)
            for checker in REGISTERED_CHECKERS:
                checker(ds)

            if not read_errors(path):
                logger.success("pass 🎉")


@register
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


@register
def coord_checker(ds: xr.Dataset) -> None:
    if (latitude := ds.get("latitude")) is None:
        logger.error("missing 'latitude' field")
    if (longitude := ds.get("longitude")) is None:
        logger.error("missing 'longitude' field")
    if (altitude := ds.get("altitude")) is None:
        logger.error("missing 'altitude' field")

    if latitude is None or longitude is None or altitude is None:
        return

    coord_units = ((latitude, "degree_north"), (longitude, "degree_east"), (altitude, "m"))
    for coord, _units in coord_units:
        if (size := coord.size) != 1:
            logger.error(f"{coord.name}.{size=} != 1")
        if (units := coord.attrs.get("units")) is None:
            logger.error(f"missing {coord.name}.units")
            continue
        if units != _units:
            logger.error(f"{coord.name}.{units=} != '{_units}'")

    if (latitude < -180).any() or (latitude > 180).any():
        logger.error(f"out of latitude range [-180, 180]")
    if (longitude < -90).any() or (longitude > 90).any():
        logger.error(f"out of longitude range [-90, 90]")


@register
def data_checker(ds: xr.Dataset) -> None:
    if (time := ds.get("time")) is None:
        logger.error("missing 'time' field")
        return

    if not set(VARIABLE_UNITS).intersection(ds.data_vars):
        logger.error("missing obs found")
        return

    for var, _units in VARIABLE_UNITS.items():
        if var not in ds.data_vars:
            continue

        if (size := ds[var].size) != time.size:
            logger.error(f"{var}.{size=} != {time.size}")
        if (units := ds[var].attrs.get("units")) is None:
            logger.error(f"missing {var}.units")
            continue
        if units != _units:
            logger.error(f"{var}.{units=} != '{_units}'")

    for var in VARIABLE_UNITS:
        if (ds[var] < 0).any():
            logger.error(f"{var} has negative values")
