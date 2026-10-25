"""Evaluation of frozen predictions without model fitting."""

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_fscore_support,
)

from microalpha.artifacts import atomic_write_json, atomic_write_parquet, refresh_run_manifest
from microalpha.train import CLASSES, predict_majority


def _one_hot(prediction: np.ndarray) -> np.ndarray:
    probability = np.zeros((len(prediction), 3))
    for column, label in enumerate(CLASSES):
        probability[:, column] = prediction == label
    return probability


def build_test_predictions(
    models: dict[str, Any], joined: pd.DataFrame, metadata: dict[str, dict]
) -> pd.DataFrame:
    rows = []
    for horizon in sorted(joined["horizon"].unique()):
        test = joined[(joined["horizon"] == horizon) & (joined["split"] == "test")].copy()
        id_columns = ["dataset_id", "event_index", "research_index", "horizon", "label"]
        id_columns.extend(name for name in ("time_seconds", "relative_spread") if name in test)
        ids = test[id_columns]
        for model_name in ("majority", "obi_rule", "logistic", "xgboost"):
            key = f"h{horizon}_{model_name}"
            model = models[key]
            if model_name == "majority":
                prediction, probability = predict_majority(model, len(test))
            elif model_name == "obi_rule":
                threshold = model["threshold"]
                prediction = np.where(
                    test["obi_l1"] > threshold, 1, np.where(test["obi_l1"] < -threshold, -1, 0)
                )
                probability = _one_hot(prediction)
            else:
                features = metadata[key]["features"]
                raw_prediction = model.predict(test[features])
                probability = model.predict_proba(test[features])
                prediction = (
                    CLASSES[raw_prediction.astype(int)]
                    if model_name == "xgboost"
                    else raw_prediction
                )
            probability = np.asarray(probability, dtype=float)
            probability /= probability.sum(axis=1, keepdims=True)
            frame = ids.rename(columns={"label": "y_true"}).copy()
            frame["model"] = model_name
            frame["split"] = "test"
            frame["y_pred"] = prediction.astype(int)
            frame[["p_down", "p_flat", "p_up"]] = probability
            rows.append(frame)
    result = pd.concat(rows, ignore_index=True)
    for horizon, horizon_rows in result.groupby("horizon"):
        groups = [tuple(group["event_index"]) for _, group in horizon_rows.groupby("model")]
        if not groups or any(ids != groups[0] for ids in groups[1:]):
            raise ValueError(f"models do not share Test IDs for horizon {horizon}")
    return result


def classification_metrics(predictions: pd.DataFrame) -> dict[str, dict]:
    output = {}
    for (horizon, model), group in predictions.groupby(["horizon", "model"]):
        true = group["y_true"].astype(int)
        predicted = group["y_pred"].astype(int)
        probability = group[["p_down", "p_flat", "p_up"]].to_numpy()
        precision, recall, _, support = precision_recall_fscore_support(
            true, predicted, labels=CLASSES, zero_division=0
        )
        target = np.eye(3)[true.map({-1: 0, 0: 1, 1: 2}).to_numpy()]
        output[f"h{horizon}_{model}"] = {
            "sample_count": len(group),
            "macro_f1": f1_score(true, predicted, labels=CLASSES, average="macro", zero_division=0),
            "balanced_accuracy": balanced_accuracy_score(true, predicted),
            "mcc": matthews_corrcoef(true, predicted),
            "log_loss": log_loss(true, probability, labels=CLASSES),
            "multiclass_brier": float(np.mean(np.sum((probability - target) ** 2, axis=1))),
            "precision": dict(zip(("down", "flat", "up"), precision.tolist(), strict=True)),
            "recall": dict(zip(("down", "flat", "up"), recall.tolist(), strict=True)),
            "support": dict(zip(("down", "flat", "up"), support.astype(int).tolist(), strict=True)),
            "confusion_matrix": confusion_matrix(true, predicted, labels=CLASSES).tolist(),
        }
    return output


def slice_report(predictions: pd.DataFrame) -> list[dict]:
    required = {"time_seconds", "relative_spread"}
    if not required <= set(predictions):
        raise ValueError(f"slice inputs missing: {sorted(required - set(predictions))}")
    frame = predictions.copy()
    frame["time_slice"] = pd.cut(
        frame["time_seconds"],
        bins=[-np.inf, 11 * 3600, 14 * 3600, np.inf],
        labels=["open", "midday", "close"],
    )
    frame["spread_slice"] = pd.cut(
        frame["relative_spread"],
        bins=[-np.inf, 0.0001, 0.0003, np.inf],
        labels=["tight", "normal", "wide"],
    )
    rows = []
    for dimensions in (("time_slice",), ("spread_slice",)):
        for key, group in frame.groupby(list(dimensions), observed=True):
            key = key if isinstance(key, tuple) else (key,)
            rows.append(
                {
                    "dimension": dimensions[0],
                    "slice": str(key[0]),
                    "sample_count": len(group),
                    "class_proportions": {
                        str(label): float((group["y_true"] == label).mean()) for label in CLASSES
                    },
                    "macro_f1": f1_score(
                        group["y_true"],
                        group["y_pred"],
                        labels=CLASSES,
                        average="macro",
                        zero_division=0,
                    ),
                    "statistical_claim": "descriptive_only_not_iid_significance",
                }
            )
    return rows


def cost_scenarios(
    *,
    fees_bps: tuple[float, ...] = (0.0, 0.5, 1.0),
    spread_fractions: tuple[float, ...] = (0.5, 1.0),
    delays: tuple[int, ...] = (0, 1, 5),
) -> dict:
    scenarios = [
        {"fee_bps": fee, "spread_fraction": spread, "delay_events": delay}
        for fee in fees_bps
        for spread in spread_fractions
        for delay in delays
    ]
    return {
        "schema_version": "1.0",
        "purpose": "signal_cost_sensitivity_only",
        "scenarios": scenarios,
        "limitations": [
            "no_fill_probability_model",
            "no_queue_position_model",
            "no_market_impact_model",
            "not_a_net_profit_claim",
        ],
    }


def evaluate_run(run_dir: str | Path, features_path: str | Path) -> dict:
    run = Path(run_dir)
    labels = pd.read_parquet(run / "labels.parquet")
    features = pd.read_parquet(features_path)
    joined = labels.merge(features, on=["dataset_id", "event_index", "research_index"])
    metadata = __import__("json").loads((run / "model_metadata.json").read_text(encoding="utf-8"))
    models = {path.stem: joblib.load(path) for path in sorted((run / "models").glob("*.joblib"))}
    predictions = build_test_predictions(models, joined, metadata)
    metrics = classification_metrics(predictions)
    slices = slice_report(predictions)
    costs = cost_scenarios()
    atomic_write_parquet(run / "predictions_test.parquet", predictions)
    atomic_write_json(run / "metrics.json", metrics)
    metric_rows = [
        {
            "model_horizon": key,
            **{
                name: value
                for name, value in item.items()
                if name
                in {
                    "sample_count",
                    "macro_f1",
                    "balanced_accuracy",
                    "mcc",
                    "log_loss",
                    "multiclass_brier",
                }
            },
        }
        for key, item in metrics.items()
    ]
    temporary_csv = run / ".metrics.csv.tmp"
    pd.DataFrame(metric_rows).to_csv(temporary_csv, index=False)
    temporary_csv.replace(run / "metrics.csv")
    atomic_write_json(run / "slice_report.json", slices)
    atomic_write_json(run / "cost_scenario.json", costs)
    refresh_run_manifest(run)
    return {
        "predictions": len(predictions),
        "metric_groups": len(metrics),
        "artifacts": [
            "predictions_test.parquet",
            "metrics.json",
            "metrics.csv",
            "slice_report.json",
            "cost_scenario.json",
        ],
    }
