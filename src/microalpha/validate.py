"""Data-quality classification for aligned event/book rows."""

from collections import Counter
from typing import Any

import pandas as pd

from microalpha.config import QualityConfig, SourceConfig


def validate_lobster(
    events: pd.DataFrame, books: pd.DataFrame, source: SourceConfig, quality: QualityConfig
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not events["event_index"].equals(books["event_index"]):
        raise ValueError("event and book indices are not positionally aligned")
    output = books.copy()
    output["time_seconds"] = events["time_seconds"].to_numpy()
    output["event_type"] = events["event_type"].to_numpy()
    reasons: list[str | None] = []
    last_time = float("-inf")
    for idx in range(len(output)):
        row = output.iloc[idx]
        event = events.iloc[idx]
        reason = None
        if event["time_seconds"] < last_time:
            reason = "time_decreased"
        last_time = event["time_seconds"]
        bid, ask = row["bid_price_1"], row["ask_price_1"]
        bid_size, ask_size = row["bid_size_1"], row["ask_size_1"]
        if event["event_type"] == 7:
            reason = reason or "trading_halt"
        elif bid <= 0 or ask <= 0 or bid_size < 0 or ask_size < 0:
            reason = reason or "invalid_price_or_size"
        elif bid > ask and quality.exclude_crossed:
            reason = reason or "crossed_book"
        elif bid == ask and quality.exclude_locked:
            reason = reason or "locked_book"
        reasons.append(reason)
    output["invalid_reason"] = pd.Series(reasons, dtype="string")
    output["eligible"] = output["invalid_reason"].isna()
    eligible_positions = output["eligible"].cumsum() - 1
    output["research_index"] = eligible_positions.where(output["eligible"], pd.NA).astype("Int64")
    counts = Counter(reason for reason in reasons if reason)
    report = {
        "schema_version": "1.0",
        "dataset_id": source.dataset_id,
        "raw_rows": len(output),
        "eligible_rows": int(output["eligible"].sum()),
        "excluded_rows": int((~output["eligible"]).sum()),
        "excluded_by_reason": dict(sorted(counts.items())),
        "first_time_seconds": float(events["time_seconds"].iloc[0]) if len(events) else None,
        "last_time_seconds": float(events["time_seconds"].iloc[-1]) if len(events) else None,
    }
    return output, report
