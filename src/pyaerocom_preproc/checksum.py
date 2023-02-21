from functools import lru_cache
from pathlib import Path

try:  # pragma: no cover
    HASHLIB = "blake3"
    from blake3 import blake3 as hasher  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    HASHLIB = "hashlib.blake2b"
    from hashlib import blake2b as hasher


__all__ = ["HASHLIB", "checksum"]


@lru_cache
def checksum(path: Path) -> str:
    _checksum = hasher()
    with path.open("rb") as f:
        # Read and update hash in chunks of 4K
        for block in iter(lambda: f.read(4096), b""):
            _checksum.update(block)
    return _checksum.hexdigest()
