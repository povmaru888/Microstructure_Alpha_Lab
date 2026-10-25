import pandas as pd
import pytest

from microalpha.config import FeatureConfig
from microalpha.features import compute_features


def test_midprice_and_spread(synthetic_books: pd.DataFrame) -> None:
    result = compute_features(synthetic_books, FeatureConfig())
    assert result.loc[0, "midprice"] == pytest.approx(100.0)
    assert result.loc[0, "spread"] == pytest.approx(0.02)
    assert result.loc[0, "relative_spread"] == pytest.approx(0.0002)


def test_invalid_row_has_null_price_features(synthetic_books: pd.DataFrame) -> None:
    books = synthetic_books.copy()
    books.loc[0, "eligible"] = False
    result = compute_features(books, FeatureConfig())
    assert pd.isna(result.loc[0, "midprice"])
    assert pd.isna(result.loc[0, "spread"])
