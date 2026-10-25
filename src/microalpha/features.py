"""Canonical, causal Python microstructure feature engine."""

import numpy as np
import pandas as pd

from microalpha.config import FeatureConfig

KEY_COLUMNS = ["dataset_id", "event_index", "research_index"]


def feature_schema(books: pd.DataFrame) -> pd.DataFrame:
    missing = [name for name in [*KEY_COLUMNS, "eligible"] if name not in books]
    if missing:
        raise ValueError(f"missing feature input columns: {missing}")
    if books.duplicated(["dataset_id", "event_index"]).any():
        raise ValueError("feature event keys must be unique")
    context_columns = [name for name in ("time_seconds", "event_type") if name in books]
    result = books[[*KEY_COLUMNS, *context_columns]].copy()
    result["feature_valid"] = books["eligible"].astype(bool)
    result["feature_invalid_reason"] = books.get(
        "invalid_reason", pd.Series(pd.NA, index=books.index, dtype="string")
    )
    return result


def compute_features(books: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    """Compute all values from the current or earlier eligible book only."""
    if max(config.depths) > max(
        int(name.rsplit("_", 1)[1]) for name in books if name.startswith("bid_size_")
    ):
        raise ValueError("feature depth exceeds available input depth")
    result = feature_schema(books)
    eligible = books["eligible"].astype(bool)
    bid, ask = books["bid_price_1"], books["ask_price_1"]
    mid = (bid + ask) / 2
    result["midprice"] = ((bid + ask) / 2).where(eligible & (mid > 0))
    result["spread"] = (ask - bid).where(eligible & (mid > 0))
    result["relative_spread"] = (result["spread"] / result["midprice"]).where(
        result["midprice"] > 0
    )
    for depth in config.depths:
        bid_sum = sum(books[f"bid_size_{level}"] for level in range(1, depth + 1))
        ask_sum = sum(books[f"ask_size_{level}"] for level in range(1, depth + 1))
        denominator = bid_sum + ask_sum
        result[f"obi_l{depth}"] = ((bid_sum - ask_sum) / denominator).where(
            eligible & (denominator > 0)
        )
    denominator = books["bid_size_1"] + books["ask_size_1"]
    result["microprice"] = (
        (ask * books["bid_size_1"] + bid * books["ask_size_1"]) / denominator
    ).where(eligible & (denominator > 0))
    result["micro_deviation"] = (
        (result["microprice"] - result["midprice"]) / result["midprice"]
    ).where(result["midprice"] > 0)
    eligible_books = books.loc[eligible]
    previous = eligible_books.shift(1)
    event = (
        (eligible_books["bid_price_1"] >= previous["bid_price_1"]) * eligible_books["bid_size_1"]
        - (eligible_books["bid_price_1"] <= previous["bid_price_1"]) * previous["bid_size_1"]
        - (eligible_books["ask_price_1"] <= previous["ask_price_1"]) * eligible_books["ask_size_1"]
        + (eligible_books["ask_price_1"] >= previous["ask_price_1"]) * previous["ask_size_1"]
    )
    result["ofi_event"] = np.nan
    result.loc[eligible_books.index, "ofi_event"] = event
    prior_raw = eligible_books["event_index"].shift(1)
    result["raw_gap_events"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    result.loc[eligible_books.index, "raw_gap_events"] = (
        eligible_books["event_index"] - prior_raw - 1
    ).astype("Int64")
    for window in config.ofi_windows:
        result[f"ofi_w{window}"] = np.nan
        rolling = event.rolling(window, min_periods=window).sum()
        result.loc[eligible_books.index, f"ofi_w{window}"] = rolling
    value_columns = [
        name
        for name in result
        if name not in [*KEY_COLUMNS, "feature_valid", "feature_invalid_reason", "raw_gap_events"]
    ]
    result.loc[~eligible, value_columns] = np.nan
    return result
