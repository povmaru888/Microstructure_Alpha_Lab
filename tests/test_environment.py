from pathlib import Path
from tomllib import loads

ROOT = Path(__file__).parents[1]


def test_supported_python_version_is_declared() -> None:
    project = loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["requires-python"] == ">=3.12"


def test_direct_dependencies_are_exactly_pinned() -> None:
    lines = [
        line
        for line in (ROOT / "requirements.lock").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    assert lines
    assert all("==" in line for line in lines)


def test_quality_tools_are_configured() -> None:
    project = loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["tool"]["ruff"]["target-version"] == "py312"
    assert project["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
