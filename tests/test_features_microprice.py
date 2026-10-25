import pandas as pd

from microalpha.config import FeatureConfig
from microalpha.features import compute_features


def test_microprice_is_inside_quotes(synthetic_books: pd.DataFrame) -> None:
    result = compute_features(synthetic_books, FeatureConfig())
    value = result.loc[0, "microprice"]
    assert synthetic_books.loc[0, "bid_price_1"] <= value <= synthetic_books.loc[0, "ask_price_1"]
    assert result.loc[0, "micro_deviation"] > 0


def test_microprice_zero_total_size_is_null(synthetic_books: pd.DataFrame) -> None:
    books = synthetic_books.copy()
    books.loc[0, ["bid_size_1", "ask_size_1"]] = 0.0
    result = compute_features(books, FeatureConfig())
    assert pd.isna(result.loc[0, "microprice"])
    assert pd.isna(result.loc[0, "micro_deviation"])
