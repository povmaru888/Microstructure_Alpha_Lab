import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from microalpha.config import load_settings
from microalpha.evaluate import evaluate_run

ROOT = Path(__file__).parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "run_experiment", ROOT / "scripts/run_experiment.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_run_experiment_writes_versioned_artifacts(tmp_path: Path) -> None:
    size = 900
    rng = np.random.default_rng(42)
    mid = 100 + np.cumsum(rng.choice([-0.02, 0, 0.02], size=size, p=[0.35, 0.3, 0.35]))
    features = pd.DataFrame(
        {
            "dataset_id": "synthetic",
            "event_index": range(size),
            "research_index": range(size),
            "feature_valid": True,
            "time_seconds": 34_200 + np.arange(size),
            "midprice": mid,
            "relative_spread": 0.0002,
            "obi_l1": rng.uniform(-1, 1, size),
            "obi_l5": rng.uniform(-1, 1, size),
            "obi_l10": rng.uniform(-1, 1, size),
            "micro_deviation": rng.normal(0, 0.0001, size),
            "ofi_event": rng.normal(size=size),
            "ofi_w10": rng.normal(size=size),
            "ofi_w20": rng.normal(size=size),
            "ofi_w50": rng.normal(size=size),
        }
    )
    features_path = tmp_path / "features.parquet"
    features.to_parquet(features_path, index=False)
    payload = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text(encoding="utf-8"))
    payload["labels"]["tick_size"] = 0.01
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    settings = load_settings(config_path)
    manifest = _module().run_experiment(settings, features_path, tmp_path / "runs", "trial")
    run = tmp_path / "runs/trial"
    assert (run / "labels.parquet").is_file()
    assert len(list((run / "models").glob("*.joblib"))) == 18
    assert len(manifest["features_sha256"]) == 64
    assert manifest["dependency_lock_sha256"]
    assert len(manifest["artifact_sha256"]) >= 15
    evaluation = evaluate_run(run, features_path)
    assert evaluation["metric_groups"] == 18
    for artifact in evaluation["artifacts"]:
        assert (run / artifact).is_file()
    refreshed = __import__("json").loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    assert "predictions_test.parquet" in refreshed["artifact_sha256"]
    assert "metrics.json" in refreshed["artifacts"]
    predictions = pd.read_parquet(run / "predictions_test.parquet")
    for _, group in predictions.groupby("horizon"):
        ids = [tuple(rows["event_index"]) for _, rows in group.groupby("model")]
        assert all(item == ids[0] for item in ids)
    with pytest.raises(FileExistsError):
        _module().run_experiment(settings, features_path, tmp_path / "runs", "trial")
