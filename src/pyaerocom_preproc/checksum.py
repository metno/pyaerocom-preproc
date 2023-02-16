from functools import lru_cache
from pathlib import Path

from blake3 import blake3


@lru_cache
def blake3sum(path: Path) -> str:
    hash = blake3()
    with path.open("rb") as f:
        # Read and update hash in chunks of 4K
        for block in iter(lambda: f.read(4096), b""):
            hash.update(block)
    return hash.hexdigest()
