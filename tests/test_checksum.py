from pathlib import Path

import pytest
from pyaerocom_preproc.checksum import HASHLIB, checksum, hasher


@pytest.fixture
def path(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "check.txt"
    path.write_text(text)
    return path


def test_HASHLIB():
    assert HASHLIB in {"blake3", "hashlib.blake2b"}


@pytest.mark.parametrize("text", ("check1", "hash2", "test3"))
def test_checksum(text: str, path: Path):
    assert checksum(path) == hasher(text.encode()).hexdigest()
