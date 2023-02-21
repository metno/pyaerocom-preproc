from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path
from platform import python_version
from textwrap import dedent
from typing import Optional

import typer
from loguru import logger

from .check_obs import obs_checker, obs_report, obs_upload
from .checksum import HASHLIB
from .config import config
from .error_db import logging_patcher

main = typer.Typer(add_completion=False)
main.command(name="check-obs")(obs_checker)
main.command(name="report-obs")(obs_report)
main.command(name="upload-obs")(obs_upload)


def version_callback(value: bool) -> None:  # pragma: no cover
    if not value:
        return

    _package = lambda name: typer.style(name, fg=typer.colors.GREEN, bold=True)
    _version = lambda name: typer.style(name, fg=typer.colors.CYAN, bold=True)

    def package(*names: str) -> str:
        return ", ".join(
            f"{_package(name)} ({_version(metadata.version(name))})" for name in names
        )

    message = f"""
        {package(__package__)}
        dependencies (installed version for {_package("Python")} {_version(python_version())})

        data formats and manipulation
        {package("xarray", "netCDF4", "numpy")}

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
            handler.update(level="WARN")
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
