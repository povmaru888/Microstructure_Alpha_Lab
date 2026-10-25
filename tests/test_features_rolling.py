import pandas as pd
import pytest

from microalpha.config import FeatureConfig
from microalpha.features import compute_features


def test_rolling_ofi_requires_complete_history(synthetic_books: pd.DataFrame) -> None:
    result = compute_features(synthetic_books, FeatureConfig())
    assert result["ofi_w10"].iloc[:10].isna().all()
    assert result.loc[10, "ofi_w10"] == pytest.approx(result["ofi_event"].iloc[1:11].sum())
    assert result["ofi_w20"].iloc[:20].isna().all()
    assert result["ofi_w50"].iloc[:50].isna().all()


def test_rolling_uses_eligible_sequence_and_is_causal(synthetic_books: pd.DataFrame) -> None:
    books = synthetic_books.copy()
    books.loc[5, "eligible"] = False
    before = compute_features(books, FeatureConfig())
    books.loc[70, "bid_size_1"] = 1_000_000
    after = compute_features(books, FeatureConfig())
    assert before.loc[:69, "ofi_w10"].equals(after.loc[:69, "ofi_w10"])
    assert pd.notna(before.loc[11, "ofi_w10"])
