from __future__ import annotations

from functools import partial
from importlib import metadata
from pathlib import Path

import pytest
from pyaerocom_preproc.cli import main
from pyaerocom_preproc.error_db import logging_patcher, read_errors
from typer.testing import CliRunner

runner = CliRunner()


def fake_s3_upload(path: Path, *, object_name: str | None = None):
    assert path.is_file()
    assert object_name is not None
    assert object_name.endswith(path.name)


@pytest.fixture(autouse=True)
def use_tmp_db(database: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "pyaerocom_preproc.cli.logging_patcher", partial(logging_patcher, database=database)
    )
    monkeypatch.setattr(
        "pyaerocom_preproc.check_obs.read_errors", partial(read_errors, database=database)
    )
    monkeypatch.setattr("pyaerocom_preproc.check_obs.s3_upload", fake_s3_upload)


@pytest.mark.parametrize("options", ("--version", "-V"))
def test_version(options: str):
    result = runner.invoke(main, options.split())
    assert result.exit_code == 0
    assert "pyaerocom_preproc" in result.output
    assert metadata.version("pyaerocom_preproc") in result.output


@pytest.mark.parametrize(
    "options",
    (
        "-q   report-obs valid tests/check_obs/valid-1D-2020.nc",
        "     report-obs valid tests/check_obs/valid-1D-2020.nc",
        "-v   report-obs valid tests/check_obs/valid-1D-2020.nc",
        "-vv  report-obs valid tests/check_obs/valid-1D-2020.nc",
        "-vvv report-obs valid tests/check_obs/valid-1D-2020.nc",
    ),
)
def test_report_obs(options: str):
    result = runner.invoke(main, options.split())
    assert result.exit_code == 0
    if options.startswith(("-q", "--quiet")):
        assert result.output == ""
    else:
        assert "pass" in result.output


def test_report_obs_clear_cache():
    options = "report-obs incomplete tests/check_obs/incomplete-1D-2020.nc"
    # first call
    result = runner.invoke(main, options.split())
    assert result.exit_code == 0
    assert "not a full year" in result.output

    # second call
    result = runner.invoke(main, options.split())
    assert result.exit_code == 0
    assert "not a full year" in result.output

    # 3rd call with chear cache
    result = runner.invoke(main, f"{options} --clear-cache".split())
    assert result.exit_code == 0
    assert "not a full year" in result.output


@pytest.mark.parametrize(
    "options",
    (
        "-q   report-obs incomplete tests/check_obs/incomplete-1D-2020.nc",
        "     report-obs incomplete tests/check_obs/incomplete-1D-2020.nc",
        "-v   report-obs incomplete tests/check_obs/incomplete-1D-2020.nc",
        "-vv  report-obs incomplete tests/check_obs/incomplete-1D-2020.nc",
        "-vvv report-obs incomplete tests/check_obs/incomplete-1D-2020.nc",
    ),
)
def test_report_obs_incomplete(options: str):
    result = runner.invoke(main, options.split())
    assert result.exit_code == 0
    assert "not a full year" in result.output


@pytest.mark.parametrize(
    "options",
    (
        "report-obs valid      tests/check_obs/incomplete-1D-2020.nc",
        "report-obs incomplete tests/check_obs/valid-1D-2020.nc",
    ),
)
def test_report_obs_inconsistent(options: str):
    result = runner.invoke(main, options.split())
    assert result.exit_code == 0
    assert "filename does not match" in result.output


def test_upload_obs():
    options = "upload-obs valid tests/check_obs/valid-1D-2020.nc"
    result = runner.invoke(main, options.split())
    assert result.exit_code == 0
    assert "pass" in result.output


def test_bucket_ls():
    options = "bucket-ls"
    result = runner.invoke(main, options)
    assert result.exit_code == 0
