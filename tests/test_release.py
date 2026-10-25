from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_release_ignores_sensitive_and_generated_paths() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("data/raw/**", "data/processed/**", "artifacts/**", ".env", ".venv/"):
        assert pattern in ignored
    fixture_names = {path.name for path in (ROOT / "tests/fixtures").iterdir()}
    assert fixture_names == {"message.csv", "orderbook_l2.csv", "orderbook_l2_mismatched.csv"}


def test_release_ci_is_cross_platform_and_complete() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "ubuntu-24.04" in workflow
    assert "windows-2022" in workflow
    assert "ctest" in workflow and "pytest -q" in workflow
    checklist = (ROOT / "docs/release_checklist.md").read_text(encoding="utf-8")
    normalized = " ".join(checklist.split())
    assert "Lawfully downloaded LOBSTER raw smoke" in normalized
    assert "400,391 aligned rows" in normalized
    assert "Windows build runners are configured" in normalized
