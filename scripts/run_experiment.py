#!/usr/bin/env python3
"""Create labels, purged splits, and frozen model artifacts."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

from microalpha.artifacts import (
    atomic_dump_joblib,
    atomic_write_json,
    atomic_write_parquet,
    reproducibility_manifest,
    sha256_file,
)
from microalpha.config import Settings, load_settings
from microalpha.labels import make_labels
from microalpha.splits import make_time_splits
from microalpha.train import fit_obi_rule, train_logistic, train_majority, train_xgboost

FEATURE_COLUMNS = [
    "relative_spread",
    "obi_l1",
    "obi_l5",
    "obi_l10",
    "micro_deviation",
    "ofi_event",
    "ofi_w10",
    "ofi_w20",
    "ofi_w50",
]


def _config_hash(settings: Settings) -> str:
    payload = json.dumps(settings.model_dump(mode="json"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def run_experiment(settings: Settings, features_path: Path, output_root: Path, run_id: str) -> dict:
    run_dir = output_root / run_id
    if run_dir.exists():
        raise FileExistsError(f"run_id already exists: {run_id}")
    features = pd.read_parquet(features_path)
    labels = make_labels(features, settings.labels)
    labelled, split_manifest = make_time_splits(
        labels, settings.split.train_frac, settings.split.valid_frac
    )
    joined = labelled.merge(features, on=["dataset_id", "event_index", "research_index"])
    available = [name for name in FEATURE_COLUMNS if name in joined]
    if not available:
        raise ValueError("no configured model features are available")
    models: dict[str, object] = {}
    metadata: dict[str, dict] = {}
    for horizon in settings.labels.horizons:
        subset = joined[(joined["horizon"] == horizon) & joined["split"].notna()]
        train = subset[subset["split"] == "train"]
        valid = subset[subset["split"] == "valid"]
        if set(train["label"].astype(int)) != {-1, 0, 1}:
            raise ValueError(f"horizon {horizon} training data must contain all three classes")
        prefix = f"h{horizon}"
        majority = train_majority(train["label"])
        models[f"{prefix}_majority"] = majority
        metadata[f"{prefix}_majority"] = majority
        obi = fit_obi_rule(train, valid)
        models[f"{prefix}_obi_rule"] = obi
        metadata[f"{prefix}_obi_rule"] = obi
        logistic = train_logistic(train, available, settings.models.random_state)
        models[f"{prefix}_logistic"] = logistic
        metadata[f"{prefix}_logistic"] = {
            "model_type": "logistic",
            "features": available,
            "classes": logistic.named_steps["model"].classes_.astype(int).tolist(),
            "selected_using": "train",
        }
        xgboost, xgb_meta = train_xgboost(train, valid, available, settings.models.random_state)
        models[f"{prefix}_xgboost"] = xgboost
        metadata[f"{prefix}_xgboost"] = {**xgb_meta, "features": available}
    run_dir.mkdir(parents=True)
    atomic_write_parquet(run_dir / "labels.parquet", labelled)
    atomic_write_json(run_dir / "split_manifest.json", split_manifest)
    for name, model in models.items():
        atomic_dump_joblib(run_dir / "models" / f"{name}.joblib", model)
    atomic_write_json(run_dir / "model_metadata.json", metadata)
    project_root = Path(__file__).parents[1]
    manifest = {
        **reproducibility_manifest(
            run_id=run_id,
            root=project_root,
            run_dir=run_dir,
            lockfile=project_root / "requirements.lock",
            source_hashes={"features": sha256_file(features_path)},
            seed=settings.project.seed,
            parameters=settings.model_dump(mode="json"),
        ),
        "dataset_id": str(features["dataset_id"].iloc[0]),
        "features_sha256": sha256_file(features_path),
        "config_sha256": _config_hash(settings),
        "models": sorted(models),
        "artifacts": ["labels.parquet", "split_manifest.json", "model_metadata.json"],
    }
    atomic_write_json(run_dir / "run_manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        settings = load_settings(args.config)
        if args.dry_run:
            if not args.features.is_file():
                raise FileNotFoundError(args.features)
        else:
            run_experiment(settings, args.features, args.output_dir, args.run_id)
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        print(f"experiment error: {error}", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
