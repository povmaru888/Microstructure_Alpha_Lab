import pandas as pd

from microalpha.train import fit_preprocessor


def test_preprocessor_fits_train_only() -> None:
    train = pd.DataFrame({"a": [0.0, 2.0], "b": [1.0, 3.0]})
    valid = pd.DataFrame({"a": [1000.0], "b": [1000.0]})
    processor = fit_preprocessor(train, ["a", "b"])
    assert processor.fitted_split == "train"
    assert processor.feature_order == ("a", "b")
    assert processor.pipeline.named_steps["scaler"].mean_.tolist() == [1.0, 2.0]
    assert processor.transform(valid).shape == (1, 2)
