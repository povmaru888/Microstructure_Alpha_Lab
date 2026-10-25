import numpy as np
import pandas as pd

from microalpha.train import (
    CLASSES,
    fit_obi_rule,
    predict_majority,
    train_logistic,
    train_majority,
    train_xgboost,
)


def test_majority_uses_train_labels_and_returns_three_probabilities() -> None:
    model = train_majority(pd.Series([-1, 0, 0, 1]))
    prediction, probability = predict_majority(model, 3)
    assert prediction.tolist() == [0, 0, 0]
    assert probability.shape == (3, 3)
    assert np.allclose(probability.sum(axis=1), 1)
    assert model["classes"] == CLASSES.tolist()


def test_xgboost_uses_validation_and_fixed_seed() -> None:
    train = pd.DataFrame(
        {
            "x": [-3, -2, -1, 0, 0.1, 1, 2, 3, -2.5, 0.2, 2.5],
            "label": [-1, -1, -1, 0, 0, 1, 1, 1, -1, 0, 1],
        }
    )
    valid = pd.DataFrame({"x": [-2.2, 0.05, 2.2], "label": [-1, 0, 1]})
    model, metadata = train_xgboost(train, valid, ["x"], random_state=7)
    assert metadata["selected_using"] == "validation"
    assert metadata["random_state"] == 7
    assert metadata["early_stopping_rounds"] == 5
    assert metadata["best_iteration"] < 30
    assert model.predict_proba(valid[["x"]]).shape == (3, 3)


def test_obi_rule_selects_on_validation_without_test() -> None:
    train = pd.DataFrame({"obi_l1": [-0.5, 0.0, 0.5], "label": [-1, 0, 1]})
    valid = pd.DataFrame({"obi_l1": [-0.25, 0.05, 0.25], "label": [-1, 0, 1]})
    model = fit_obi_rule(train, valid)
    assert model["threshold"] in (0.1, 0.2, 0.3)
    assert model["selected_using"] == ["train", "valid"]


def test_logistic_pipeline_has_scaler_and_probabilities() -> None:
    train = pd.DataFrame({"x": [-2.0, -1.0, 0.0, 0.1, 1.0, 2.0], "label": [-1, -1, 0, 0, 1, 1]})
    model = train_logistic(train, ["x"])
    probability = model.predict_proba(train[["x"]])
    assert "scaler" in model.named_steps
    assert model.named_steps["model"].classes_.tolist() == CLASSES.tolist()
    assert np.allclose(probability.sum(axis=1), 1)
