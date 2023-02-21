from pathlib import Path

import pytest

text_tests = pytest.mark.parametrize("text", ("check1", "hash2", "test3"))


@pytest.fixture
def path(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "check.txt"
    path.write_text(text)
    return path
