"""Event-time midprice direction labels."""

import numpy as np
import pandas as pd

from microalpha.config import LabelConfig


def make_labels(features: pd.DataFrame, config: LabelConfig) -> pd.DataFrame:
    if config.threshold_mode != "half_tick_over_mid" or config.tick_size is None:
        raise ValueError("verified tick_size is required")
    rows = []
    valid = features.loc[features["feature_valid"] & features["midprice"].notna()].reset_index(
        drop=True
    )
    for horizon in config.horizons:
        future = valid["midprice"].shift(-horizon)
        returns = np.log(future / valid["midprice"])
        threshold = (config.tick_size / 2) / valid["midprice"]
        label = pd.Series(pd.NA, index=valid.index, dtype="Int8")
        has_future = future.notna()
        label.loc[has_future & (returns > threshold)] = 1
        label.loc[has_future & (returns < -threshold)] = -1
        label.loc[has_future & (returns.abs() <= threshold)] = 0
        frame = valid[["dataset_id", "event_index", "research_index"]].copy()
        frame["horizon"] = horizon
        frame["forward_log_return"] = returns
        frame["threshold"] = threshold
        frame["label"] = label
        frame["label_end_research_index"] = valid["research_index"].shift(-horizon).astype("Int64")
        frame["label_end_event_index"] = valid["event_index"].shift(-horizon).astype("Int64")
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)
