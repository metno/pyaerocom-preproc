from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--pya-pp-obs",
        nargs="?",
        action="store",
        default=None,
        const=".*.nc",
        help="obs dataset regex",
    )


def pytest_collect_file(parent: pytest.Collector, file_path: Path):
    pya_pp = parent.config.getoption("--pya-pp-obs")
    if pya_pp is not None and re.match(pya_pp, file_path.name):
        return ObsFile.from_parent(parent, path=file_path)


class ObsFile(pytest.File):
    def collect(self):
        yield CheckFile.from_parent(
            self.parent, name="file_exists", check_func=check_file_exists, path=self.path
        )


class CheckFile(pytest.Item):
    def __init__(self, *, check_func: Callable[[Path], None], **kwargs):
        super().__init__(**kwargs)
        self.check_func = check_func

    def runtest(self):
        self.check_func(self.path)

    def reportinfo(self):
        return self.path, None, self.name


def check_file_exists(path: Path):
    assert path.exists(), f"missing {path.name}"
    assert path.is_file(), f"{path.name} is not a file"
