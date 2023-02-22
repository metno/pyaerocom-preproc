from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, List, Literal

import numpy as np
import typer
import xarray as xr
from loguru import logger

from .error_db import DB_PATH, read_errors
from .s3_bucket import s3_upload

__all__ = ["obs_report"]

VARIABLE_UNITS = dict(
    air_quality_index={"1"},
    CO_density={"mg/m3", "mg m-3"},
    NO2_density={"ug/m3", "ug m-3"},
    O3_density={"ug/m3", "ug m-3"},
    PM10_density={"ug/m3", "ug m-3"},
    PM2p5_density={"ug/m3", "ug m-3"},
    SO2_density={"ug/m3", "ug m-3"},
)


REGISTERED_CHECKERS: list[Callable[[xr.Dataset], None]] = []


def register(func):
    REGISTERED_CHECKERS.append(func)
    return func


def _check(path: Path) -> bool:
    """Check requirements for observations datasets"""
    ds = xr.open_dataset(path)

    with logger.contextualize(path=path):
        for checker in REGISTERED_CHECKERS:
            checker(ds)

        if errors := read_errors(path):
            logger.debug(f"{len(errors)} errors")

    return not errors


def _report(path: Path) -> bool:
    """Report known errors from previous checks"""
    if not (errors := read_errors(path)):
        return True

    with logger.contextualize(path=path):
        for func_name, message in errors:
            logger.patch(
                lambda record: record.update(function=func_name)  # type:ignore[call-arg]
            ).error(message)
        logger.debug(f"{len(errors)} errors")

    return False


def obs_report(
    data_set: str,
    files: List[Path],
    clear_cache: bool = typer.Option(
        False, "--clear-cache", help="clear cached errors and rerun check"
    ),
):
    """Report known errors from previous checks, files without known errors will be re-tested."""
    if clear_cache:
        DB_PATH.unlink(missing_ok=True)

    regex = re.compile(rf"{data_set}.*.nc")
    for path in files:
        if not regex.match(path.name):
            logger.bind(path=path).error(f"filename does not match r'{regex.pattern}', skip")
            continue

        if _report(path) and _check(path):
            logger.bind(path=path).success("pass 🎉")


def obs_upload(data_set: str, files: List[Path]):
    """Upload files without known errors from previous checks

    Files without known errors will be re-tested
    """
    regex = re.compile(rf"{data_set}-.*-(?P<year>\d\d\d\d).nc")
    for path in files:
        if (match := regex.search(path.name)) is None:
            logger.bind(path=path).error(f"could not infer year from filename, skip")
            continue

        if _report(path) and _check(path):
            year = match.group("year")
            s3_upload(path, object_name=f"{data_set}/download/{year}/{path.name}")


@register
def time_checker(ds: xr.Dataset) -> None:
    if (datetime_start := ds.get("datetime_start")) is None:
        logger.error("missing 'datetime_start' field")
    if (datetime_stop := ds.get("datetime_stop")) is None:
        logger.error("missing 'datetime_stop' field")

    if datetime_start is None or datetime_stop is None:
        return

    if datetime_start.dims != ("time",):
        logger.error(f"{datetime_start.dims=} != ('time',)")
    if datetime_stop.dims != ("time",):
        logger.error(f"{datetime_stop.dims=} != ('time',)")

    if not (datetime_start.dims == datetime_stop.dims == ("time",)):
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
    if freq in records and datetime_start.size < records[freq]:
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

    if (latitude < -90).any() or (latitude > 90).any():
        logger.error(f"out of latitude range [-90, 90]")
    if (longitude < -180).any() or (longitude > 180).any():
        logger.error(f"out of longitude range [-180, 180]")


@register
def data_checker(ds: xr.Dataset) -> None:
    if not set(VARIABLE_UNITS).intersection(ds.data_vars):
        logger.error("missing obs found")
        return

    for var, _units in VARIABLE_UNITS.items():
        if var not in ds.data_vars:
            continue

        if (dims := ds[var].dims) != ("time",):
            logger.error(f"{var}.{dims=} != ('time',)")
        if (units := ds[var].attrs.get("units")) is None:
            logger.error(f"missing {var}.units")
            continue
        if units not in _units:
            logger.error(f"{var}.{units=} not in {sorted(_units)}")

    for var in VARIABLE_UNITS:
        if var not in ds.data_vars:
            continue
        if (ds[var] < 0).any():
            logger.error(f"{var} has negative values")
