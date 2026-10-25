import pandas as pd

from microalpha.config import FeatureConfig, LabelConfig
from microalpha.features import compute_features
from microalpha.labels import make_labels
from microalpha.splits import make_time_splits


def test_event_time_labels_and_tail_nulls(synthetic_books: pd.DataFrame) -> None:
    features = compute_features(synthetic_books, FeatureConfig())
    labels = make_labels(
        features,
        LabelConfig(horizons=(10, 20, 50), threshold_mode="half_tick_over_mid", tick_size=0.01),
    )
    h10 = labels[labels["horizon"] == 10].reset_index(drop=True)
    assert h10.loc[0, "label_end_event_index"] == 10
    assert h10.iloc[-10:]["label"].isna().all()
    assert set(labels["label"].dropna().unique()) <= {-1, 0, 1}


def test_chronological_split_purges_crossing_labels(synthetic_books: pd.DataFrame) -> None:
    features = compute_features(synthetic_books, FeatureConfig())
    labels = make_labels(
        features, LabelConfig(horizons=(10,), threshold_mode="half_tick_over_mid", tick_size=0.01)
    )
    split, manifest = make_time_splits(labels)
    train = split[split["split"] == "train"]
    valid = split[split["split"] == "valid"]
    test = split[split["split"] == "test"]
    assert train["label_end_research_index"].max() < manifest["boundaries"]["train_end_exclusive"]
    assert valid["research_index"].min() >= manifest["boundaries"]["train_end_exclusive"]
    assert valid["label_end_research_index"].max() < manifest["boundaries"]["valid_end_exclusive"]
    assert test["research_index"].min() >= manifest["boundaries"]["valid_end_exclusive"]
