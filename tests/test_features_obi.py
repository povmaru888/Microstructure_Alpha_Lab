import pandas as pd
import pytest

from microalpha.config import FeatureConfig
from microalpha.features import compute_features


def test_obi_depths_and_hand_calculation(synthetic_books: pd.DataFrame) -> None:
    books = synthetic_books.copy()
    books.loc[0, ["bid_size_1", "ask_size_1"]] = [900.0, 300.0]
    result = compute_features(books, FeatureConfig())
    assert result.loc[0, "obi_l1"] == pytest.approx(0.5)
    assert {"obi_l1", "obi_l5", "obi_l10"} <= set(result)


def test_obi_zero_denominator_is_null(synthetic_books: pd.DataFrame) -> None:
    books = synthetic_books.copy()
    books.loc[0, ["bid_size_1", "ask_size_1"]] = 0.0
    assert pd.isna(compute_features(books, FeatureConfig()).loc[0, "obi_l1"])


def test_depth_beyond_input_fails(synthetic_books: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="exceeds available"):
        compute_features(synthetic_books, FeatureConfig(depths=(11,)))
