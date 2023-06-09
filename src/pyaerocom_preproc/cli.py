from __future__ import annotations

import sys
from functools import partial
from importlib import metadata
from pathlib import Path
from platform import python_version
from textwrap import dedent
from typing import List, Optional

import typer
from loguru import logger

from .check_obs import obs_report
from .checksum import HASHLIB
from .config import config
from .error_db import logging_patcher
from .s3_bucket import s3_list

main = typer.Typer(add_completion=False)


def version_callback(value: bool) -> None:
    if not value:
        return

    _package = partial(typer.style, fg=typer.colors.GREEN, bold=True)
    _version = partial(typer.style, fg=typer.colors.CYAN, bold=True)

    def package(*names: str) -> str:
        return ", ".join(
            f"{_package(name)} ({_version(metadata.version(name))})" for name in names
        )

    message = f"""
        {package(__package__)}
        dependencies (installed version for {_package("Python")} {_version(python_version())})

        data formats and manipulation
        {package("netCDF4", "xarray", "pandas", "numpy")}

        hashes / checksum
        {_package(HASHLIB) if HASHLIB.startswith("hashlib") else package(HASHLIB)}
                
        configuration
        {package("dynaconf", "tomli-w")}

        command line
        {package("typer", "click")}
        """

    typer.echo(dedent(message))
    raise typer.Exit()


def logging_config(verbose: int = 0, *, quiet: bool = False, debug: bool = False):
    if not debug:
        handler = dict(
            sink=sys.stdout,
            level="DEBUG",
            format="<green>{extra[path].name: <40}</green> - <cyan>{function: <12}</cyan> - <level>{message}</level>",
        )
        if quiet:
            handler.update(level="WARNING")
        elif verbose == 0:
            handler.update(level="INFO")
        elif verbose == 1:
            handler.update(level="DEBUG")
        else:
            handler.update(format="{time:%F %T} <level>{message}</level>")
        logger.configure(
            handlers=[handler], extra={"path": Path(__file__)}, patcher=logging_patcher()
        )

    logger.debug(
        f"{__package__} version {metadata.version(__package__)}, Python {python_version()}"
    )


@main.callback()
def callback(
    version: Optional[bool] = typer.Option(None, "--version", "-V", callback=version_callback),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="only show warning and error messages"
    ),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="show debug messages"),
    debug: bool = typer.Option(False, "--debug", "-d", help="show messages with line numbers"),
):
    """Check and upload observations and model data for PyAerocom usage"""
    logging_config(verbose, quiet=quiet, debug=debug)


@main.command(help=config.__doc__)
def check_s3(overwrite: bool = typer.Option(False, "--overwrite", "-O")):
    if config(overwrite=overwrite) is None:
        raise typer.Abort()


@main.command()
def report_obs(
    data_set: str,
    files: List[Path],
    clear_cache: bool = typer.Option(
        False, "--clear-cache", help="clear cached errors and rerun check"
    ),
):
    """Report known errors from previous checks, files without known errors will be re-tested."""
    obs_report(data_set, files, clear_cache=clear_cache)


@main.command()
def upload_obs(data_set: str, files: List[Path]):
    """Upload files without known errors from previous checks

    Files without known errors will be re-tested
    """
    obs_report(data_set, files, upload=True)


@main.command()
def bucket_ls():
    """List up to 1000 items in the S3 bucket"""
    s3_list()
