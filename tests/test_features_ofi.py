import pandas as pd
import pytest

from microalpha.config import FeatureConfig
from microalpha.features import compute_features


def test_ofi_first_null_and_unchanged_quotes(synthetic_books: pd.DataFrame) -> None:
    result = compute_features(synthetic_books, FeatureConfig())
    assert pd.isna(result.loc[0, "ofi_event"])
    expected = (
        synthetic_books.loc[1, "bid_size_1"]
        - synthetic_books.loc[0, "bid_size_1"]
        - synthetic_books.loc[1, "ask_size_1"]
        + synthetic_books.loc[0, "ask_size_1"]
    )
    assert result.loc[1, "ofi_event"] == pytest.approx(expected)


def test_ofi_bid_price_increase_uses_new_bid_size(synthetic_books: pd.DataFrame) -> None:
    books = synthetic_books.copy()
    books.loc[1, "bid_price_1"] = books.loc[0, "bid_price_1"] + 0.01
    result = compute_features(books, FeatureConfig())
    expected = books.loc[1, "bid_size_1"] - books.loc[1, "ask_size_1"] + books.loc[0, "ask_size_1"]
    assert result.loc[1, "ofi_event"] == pytest.approx(expected)


def test_ofi_records_raw_gap(synthetic_books: pd.DataFrame) -> None:
    books = synthetic_books.copy()
    books.loc[1, "eligible"] = False
    result = compute_features(books, FeatureConfig())
    assert result.loc[2, "raw_gap_events"] == 1
