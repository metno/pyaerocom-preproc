from pathlib import Path

from pyaerocom_preproc.checksum import HASHLIB, checksum, hasher

from .conftest import text_tests


def test_HASHLIB():
    assert HASHLIB in {"blake3", "hashlib.blake2b"}


@text_tests
def test_checksum(text: str, path: Path):
    assert checksum(path) == hasher(text.encode()).hexdigest()
