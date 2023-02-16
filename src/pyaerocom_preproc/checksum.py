import hashlib
from functools import lru_cache
from pathlib import Path


@lru_cache
def md5sum(path: Path) -> str:
    hash = hashlib.md5()
    with path.open("rb") as f:
        # Read and update hash in chunks of 4K
        for block in iter(lambda: f.read(4096), b""):
            hash.update(block)
    return hash.hexdigest()
