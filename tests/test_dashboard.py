import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("dashboard", ROOT / "app/dashboard.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_dashboard_has_four_pages_and_clear_missing_files(tmp_path: Path) -> None:
    dashboard = _module()
    assert dashboard.PAGES == (
        "Market & Depth",
        "Features",
        "Model Evaluation",
        "Benchmark & Limitations",
    )
    with pytest.raises(FileNotFoundError, match="missing run artifacts"):
        dashboard.load_run(str(tmp_path), str(tmp_path), "fingerprint")


def test_dashboard_source_contains_no_training_or_writes() -> None:
    source = (ROOT / "app/dashboard.py").read_text(encoding="utf-8")
    assert ".fit(" not in source
    assert "to_parquet(" not in source
    assert "write_text(" not in source


def test_dashboard_always_declares_limitations_and_fingerprint_cache() -> None:
    dashboard = _module()
    assert "Single-day" in dashboard.RESEARCH_NOTICE
    assert "not live trading" in dashboard.RESEARCH_NOTICE
    source = (ROOT / "app/dashboard.py").read_text(encoding="utf-8")
    assert "fingerprint" in source
    assert "eligible=" in source
    assert "schema=" in source
