from __future__ import annotations

from pathlib import Path

import loguru
import xarray as xr
from pyaerocom_preproc.check_obs import coord_checker
from pyaerocom_preproc.error_db import read_errors


def test_coord_checker(good_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=good_nc):
        coord_checker(xr.open_dataset(good_nc))
    assert read_errors(good_nc, database=database) == []


def test_empty(empty_nc: Path, patched_logger: loguru.Logger, database: Path):
    with patched_logger.contextualize(path=empty_nc):
        coord_checker(xr.open_dataset(empty_nc))

    assert set(read_errors(empty_nc, database=database)) == {
        ("coord_checker", "missing 'latitude' field"),
        ("coord_checker", "missing 'longitude' field"),
        ("coord_checker", "missing 'altitude' field"),
    }


def test_wrong_coords(wrong_coords_nc: Path, patched_logger: loguru.Logger, database: Path):
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
