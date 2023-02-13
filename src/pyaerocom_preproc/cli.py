from __future__ import annotations

from importlib import metadata
from textwrap import dedent
from typing import Optional

import typer
from dynaconf import ValidationError

from .config import settings

main = typer.Typer(add_completion=False)


def version_callback(value: bool) -> None:  # pragma: no cover
    if not value:
        return

    def _package(name: str) -> str:
        return typer.style(name, fg=typer.colors.GREEN, bold=True)

    def _version(name: str) -> str:
        return typer.style(metadata.version(name), fg=typer.colors.CYAN, bold=True)

    def package(*names: str) -> str:
        return ", ".join(f"{_package(name)} ({_version(name)})" for name in names)

    message = f"""
        {package(__package__)}
        dependencies (installed version)
        
        configuration
        {package("dynaconf")}

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
def config():
    """Check/save credentials"""
    try:
        settings.validators.validate("s3_bucket")
    except ValidationError as e:
        print(str(e))
        raise typer.Abort()
