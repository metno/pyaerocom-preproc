from __future__ import annotations

import sys
from getpass import getpass
from importlib import metadata
from pathlib import Path
from shlex import split
from textwrap import dedent
from typing import List, Optional

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

import pytest
import tomli_w
import typer

from .config import SECRETS_PATH

main = typer.Typer(add_completion=False)


def version_callback(value: bool) -> None:  # pragma: no cover
    if not value:
        return

    def _package(name: str) -> str:
        return typer.style(name, fg=typer.colors.GREEN, bold=True)

    def _version(name: str) -> str:
        return typer.style(metadata.version(name), fg=typer.colors.CYAN, bold=True)

    def package(*names: str | None) -> str:
        return ", ".join(f"{_package(name)} ({_version(name)})" for name in names if name)

    message = f"""
        {package(__package__)}
        dependencies (installed version)
        
        configuration
        {package("dynaconf", "tomli" if sys.version_info < (3, 11) else None, "tomli-w")}

        command line
        {package("typer", "click")}
        """

    typer.echo(dedent(message))
    raise typer.Exit()


@main.callback()
def callback(
    version: Optional[bool] = typer.Option(None, "--version", "-V", callback=version_callback),
):
    """Check and upload observations and model data for PyAerocom usage"""


@main.command()
def config(
    overwrite: bool = typer.Option(False, "--overwrite", "-O"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
):
    """Check credentials file"""
    if not SECRETS_PATH.exists() or overwrite:
        secrets = {key: getpass(f"{key}: ") for key in ("bucket_name", "key_id", "access_key")}
        SECRETS_PATH.parent.mkdir(True, exist_ok=True)
        SECRETS_PATH.write_text(tomli_w.dumps({"s3_bucket": secrets}))
        SECRETS_PATH.chmod(0o600)  # only user has read/write permissions

    cmd = f"{'' if quiet else '-vv'} --tb=no tests/test_s3_bucket.py::test_credentials".split()
    if exit_code := pytest.main(cmd) != 0:
        sys.exit(exit_code)


@main.command()
def check_obs(
    data_set: str,
    files: List[Path],
    quiet: bool = typer.Option(False, "--quiet", "-q"),
):
    """Check requirements for observations datasets"""
    cmd = split(f"{'' if quiet else '-vv'} --tb=no --pya-pp-obs '{data_set}.*.nc'")
    cmd.extend(path.resolve() for path in files)  # type:ignore
    if exit_code := pytest.main(cmd) != 0:
        sys.exit(exit_code)
