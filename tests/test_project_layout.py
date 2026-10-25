from pathlib import Path

import microalpha

ROOT = Path(__file__).parents[1]


def test_src_layout_package_is_importable() -> None:
    assert microalpha.__version__ == "0.1.0"
    assert (ROOT / "src/microalpha/__init__.py").is_file()


def test_generated_and_restricted_paths_are_ignored() -> None:
    rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for required in ("data/raw/**", "data/processed/**", "artifacts/**", ".env"):
        assert required in rules


def test_project_is_not_nested_in_unrelated_repository() -> None:
    assert "AI_Quant_Research" not in str(ROOT)
