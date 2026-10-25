import pandas as pd
import pytest

from microalpha.features import feature_schema


def test_schema_has_unique_keys_and_invalid_null_state(synthetic_books: pd.DataFrame) -> None:
    books = synthetic_books.copy()
    books.loc[2, "eligible"] = False
    books["invalid_reason"] = pd.Series(
        [pd.NA, pd.NA, "locked_book"] + [pd.NA] * 77, dtype="string"
    )
    result = feature_schema(books)
    assert list(result.columns) == [
        "dataset_id",
        "event_index",
        "research_index",
        "time_seconds",
        "feature_valid",
        "feature_invalid_reason",
    ]
    assert not result.loc[2, "feature_valid"]
    assert result.loc[2, "feature_invalid_reason"] == "locked_book"


def test_duplicate_feature_keys_fail(synthetic_books: pd.DataFrame) -> None:
    books = pd.concat([synthetic_books, synthetic_books.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="must be unique"):
        feature_schema(books)
