from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def in_tmp(tmp_path, monkeypatch) -> Path:
    """Run the test from an empty directory so default build/ paths land in tmp."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
