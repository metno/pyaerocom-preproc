from __future__ import annotations

from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--pya-pp-files", action="store", nargs="+", type=Path, help="pya-pp files to test"
    )


def pya_pp_param(path: Path | None) -> pytest.ParameterSet:
    if path is not None:
        return pytest.param(path, id=path.name)

    return pytest.param(None, id="no files to test", marks=pytest.mark.skip("no pya-pp files"))


def pytest_generate_tests(metafunc: pytest.Metafunc):
    if "pya_pp_file" in metafunc.fixturenames:
        files: list[Path | None] = metafunc.config.getoption("--pya-pp-files") or [None]
        metafunc.parametrize("pya_pp_file", (pya_pp_param(path) for path in files))
