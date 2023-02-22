from pathlib import Path

from pyaerocom_preproc.checksum import HASHLIB, checksum, hasher


def test_HASHLIB():
    assert HASHLIB in {"blake3", "hashlib.blake2b"}


def test_checksum(text: str, path: Path):
    assert checksum(path) == hasher(text.encode()).hexdigest()
