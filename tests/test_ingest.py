from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from microalpha.config import SourceConfig
from microalpha.ingest import IngestError, ingest_lobster


def _config(fixture_dir: Path, book: str = "orderbook_l2.csv") -> SourceConfig:
    return SourceConfig(
        provider="lobster",
        dataset_id="synthetic",
        symbol="TEST",
        trade_date=date(2026, 1, 2),
        levels=2,
        price_scale=10_000,
        message_path=fixture_dir / "message.csv",
        orderbook_path=fixture_dir / book,
    )


def test_ingest_preserves_order_timestamp_and_scales(fixture_dir: Path) -> None:
    events, books = ingest_lobster(_config(fixture_dir))
    assert events["event_index"].tolist() == list(range(6))
    assert events.loc[0, "time_seconds"] == events.loc[1, "time_seconds"]
    assert events.loc[0, "price"] == 100.0
    assert books.loc[0, "ask_price_1"] == 100.01
    assert events["raw_row_index"].equals(pd.Series(range(6), name="raw_row_index"))


def test_ingest_rejects_row_mismatch(fixture_dir: Path) -> None:
    with pytest.raises(IngestError, match="row count mismatch"):
        ingest_lobster(_config(fixture_dir, "orderbook_l2_mismatched.csv"))
