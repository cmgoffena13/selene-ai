import tomllib
from pathlib import Path

from src.utils import ensure_dir, get_version


def test_get_version_matches_pyproject() -> None:
    root = Path(__file__).resolve().parents[3]
    with (root / "pyproject.toml").open("rb") as f:
        expected = tomllib.load(f)["project"]["version"]
    assert get_version() == expected


def test_ensure_dir_creates_and_returns_path(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b"
    assert not target.exists()
    out = ensure_dir(target)
    assert out == target
    assert target.is_dir()
