from pathlib import Path


def test_file_exists(pya_pp_file: Path):
    assert pya_pp_file.exists(), f"missing {pya_pp_file.name}"
    assert pya_pp_file.is_file(), f"{pya_pp_file.name} is not a file"
