import pandas as pd

from microalpha.benchmark import compare_features, python_loop_features
from microalpha.config import FeatureConfig
from microalpha.features import compute_features


def test_python_loop_matches_vectorized_input_contract(synthetic_books: pd.DataFrame) -> None:
    vectorized = compute_features(synthetic_books, FeatureConfig())
    loop = python_loop_features(synthetic_books)
    assert compare_features(vectorized, loop)["status"] == "passed"
