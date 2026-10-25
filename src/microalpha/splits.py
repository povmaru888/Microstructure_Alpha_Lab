"""Chronological split construction with label-window purging."""

import pandas as pd


def make_time_splits(
    labels: pd.DataFrame, train_frac: float = 0.6, valid_frac: float = 0.2
) -> tuple[pd.DataFrame, dict]:
    if train_frac <= 0 or valid_frac <= 0 or train_frac + valid_frac >= 1:
        raise ValueError("invalid split fractions")
    result = labels.copy()
    max_index = int(result["research_index"].max()) + 1
    train_end = int(max_index * train_frac)
    valid_end = int(max_index * (train_frac + valid_frac))
    result["split"] = pd.Series(pd.NA, index=result.index, dtype="string")
    valid_label = result["label"].notna()
    result.loc[
        valid_label
        & (result["research_index"] < train_end)
        & (result["label_end_research_index"] < train_end),
        "split",
    ] = "train"
    result.loc[
        valid_label
        & (result["research_index"] >= train_end)
        & (result["research_index"] < valid_end)
        & (result["label_end_research_index"] < valid_end),
        "split",
    ] = "valid"
    result.loc[valid_label & (result["research_index"] >= valid_end), "split"] = "test"
    manifest = {
        "schema_version": "1.0",
        "method": "chronological_purged",
        "boundaries": {"train_end_exclusive": train_end, "valid_end_exclusive": valid_end},
        "counts": {key: int((result["split"] == key).sum()) for key in ("train", "valid", "test")},
        "purged_or_unlabelled": int(result["split"].isna().sum()),
    }
    return result, manifest
