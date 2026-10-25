import importlib.util
from pathlib import Path

import pandas as pd
import yaml

from microalpha.config import load_settings

ROOT = Path(__file__).parents[1]


def _prepare_function():
    spec = importlib.util.spec_from_file_location("prepare_data", ROOT / "scripts/prepare_data.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.prepare


def test_prepare_pipeline_is_deterministic(fixture_dir: Path, tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text(encoding="utf-8"))
    payload["source"].update(
        {
            "dataset_id": "synthetic",
            "levels": 2,
            "message_path": str(fixture_dir / "message.csv"),
            "orderbook_path": str(fixture_dir / "orderbook_l2.csv"),
        }
    )
    payload["features"]["depths"] = [1, 2]
    payload["features"]["ofi_windows"] = [2]
    payload["labels"]["tick_size"] = 0.01
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(payload), encoding="utf-8")
    settings = load_settings(config)
    prepare = _prepare_function()
    first = prepare(
        settings,
        tmp_path / "one",
        source_page="https://example.test",
        license_note="synthetic",
        downloaded_at_utc="2026-01-02T03:04:05Z",
    )
    second = prepare(
        settings,
        tmp_path / "two",
        source_page="https://example.test",
        license_note="synthetic",
        downloaded_at_utc="2026-01-02T03:04:05Z",
    )
    assert first == second
    pd.testing.assert_frame_equal(
        pd.read_parquet(tmp_path / "one/features.parquet"),
        pd.read_parquet(tmp_path / "two/features.parquet"),
    )
    assert first["feature_version"] == "1.0"
    assert first["source_sha256"]["message"]
    assert "time_seconds" in first["columns"]
    manifest = __import__("json").loads(
        (tmp_path / "one/data_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["downloaded_at_utc"] == "2026-01-02T03:04:05Z"
