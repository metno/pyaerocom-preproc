from __future__ import annotations

from enum import Enum
from pathlib import Path

import numpy as np
import pandas as pd
import typer
import xarray as xr
from pyaerocom_preproc.check_obs import VARIABLE_UNITS

app = typer.Typer(add_completion=False)


class Freq(str, Enum):
    DAILY = "1D"
    HOURLY = "1H"

    def __str__(self) -> str:
        return self.value


def datetime_start(year: int, freq: Freq) -> xr.DataArray:
    data = pd.date_range(f"{year}-01-01 00:00", f"{year}-12-31 23:00", freq=freq)
    da = xr.DataArray(data, dims="time", name="datetime_start")
    return da.reset_coords().drop_vars("time")["datetime_start"]


def datetime_stop(year: int, freq: Freq) -> xr.DataArray:
    start = {"1H": f"{year}-01-01 01:00", "1D": f"{year}-01-02 00:00"}
    data = pd.date_range(start[freq], f"{year+1}-01-01 00:00", freq=freq)
    da = xr.DataArray(data, dims="time", name="datetime_stop")
    return da.reset_coords().drop_vars("time")["datetime_stop"]


def mep_ds(year: int, freq: Freq) -> xr.Dataset:
    start, stop = datetime_start(year, freq), datetime_stop(year, freq)

    def dummy(**attrs):
        return xr.DataArray(np.full_like(start, None, dtype=float), dims="time", attrs=attrs)

    data = dict(
        datetime_start=start,
        datetime_stop=stop,
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
    ds = xr.Dataset(data)
    for var in VARIABLE_UNITS:
        ds[var].encoding.update(_FillValue=None)
    return ds


def write_empty_ds(root: Path, *, overwrite: bool = False) -> None:
    path = root / "empty.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    xr.Dataset().to_netcdf(path)


def write_mep_ds(year: int, freq: Freq, root: Path, *, overwrite: bool = False) -> None:
    path = root / f"valid-{freq}-{year}.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    mep_ds(year, freq).to_netcdf(path)


def write_wrong_coords(year: int, freq: Freq, root: Path, *, overwrite: bool = False) -> None:
    path = root / f"wrong_coords-{freq}-{year}.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    ds = mep_ds(year, freq)

    def dummy(value, **attrs):
        return xr.DataArray(np.full_like(ds["time"], value, dtype=float), dims="time", attrs=attrs)

    data = dict(
        latitude=dummy(-100, units="degN"),  # wrong unit
        longitude=dummy(360, units="degE"),  # wrong unit
        altitude=dummy(0),  # missing unit
    )
    xr.Dataset(data).to_netcdf(path)


def write_wrong_dims(year: int, freq: Freq, root: Path, *, overwrite: bool = False) -> None:
    path = root / f"wrong_dims-{freq}-{year}.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    mep_ds(year, freq).expand_dims(dict(latitude=1, longitude=1)).to_netcdf(path)


def wirte_wrong_units(year: int, freq: Freq, root: Path, *, overwrite: bool = False) -> None:
    path = root / f"wrong_units-{freq}-{year}.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    ds = mep_ds(year, freq)
    del ds["air_quality_index"].attrs["units"]  # missing unit
    ds["CO_density"].attrs["units"] = "ug/m3"  # wrong unit
    ds.to_netcdf(path)


def wrirte_negative_density(year: int, freq: Freq, root: Path, *, overwrite: bool = False) -> None:
    path = root / f"negative_density-{freq}-{year}.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    vars = dict(
        CO_density=-1,
        NO2_density=-1,
        O3_density=-1,
        PM10_density=-1,
        PM2p5_density=-1,
        SO2_density=-1,
    )
    ds = mep_ds(year, freq).drop_vars("air_quality_index")
    xr.full_like(ds, vars, dtype=np.float32).to_netcdf(
        path, encoding={var: dict(_FillValue=None) for var in vars}
    )


def write_bad_times(year: int, freq: Freq, root: Path, *, overwrite: bool = False) -> None:
    path = root / f"bad_times-{freq}-{year}.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    ds = mep_ds(year, freq)
    ds.assign(
        datetime_start=ds["datetime_start"].roll(time=7),
        datetime_stop=ds["datetime_stop"].roll(time=-7),
    ).to_netcdf(path)


def write_wrong_years(year: int, freq: Freq, root: Path, *, overwrite: bool = False) -> None:
    path = root / f"wrong_years-{freq}-{year}.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    ds = mep_ds(year, freq)
    ds.assign(datetime_start=ds["datetime_stop"]).to_netcdf(
        path, encoding={var: dict(_FillValue=None) for var in VARIABLE_UNITS}
    )


def write_incomplete(year: int, freq: Freq, root: Path, *, overwrite: bool = False) -> None:
    path = root / f"incomplete-{freq}-{year}.nc"
    if path.exists() and not overwrite:
        print(f"{path.name} found, skip")
        return

    mep_ds(year, freq).isel(time=slice(None, None, 2)).to_netcdf(path)


@app.command()
def main(
    year: int = 2020,
    freq: Freq = Freq.DAILY,
    root: Path = Path("tests/check_obs"),
    overwrite: bool = typer.Option(False, "--overwrite", "-O"),
) -> None:
    write_empty_ds(root, overwrite=overwrite)
    write_mep_ds(year, freq, root, overwrite=overwrite)
    write_wrong_coords(year, freq, root, overwrite=overwrite)
    write_wrong_dims(year, freq, root, overwrite=overwrite)
    wirte_wrong_units(year, freq, root, overwrite=overwrite)
    wrirte_negative_density(year, freq, root, overwrite=overwrite)
    write_bad_times(year, freq, root, overwrite=overwrite)
    write_wrong_years(year, freq, root, overwrite=overwrite)
    write_incomplete(year, freq, root, overwrite=overwrite)


if __name__ == "__main__":
    app()
