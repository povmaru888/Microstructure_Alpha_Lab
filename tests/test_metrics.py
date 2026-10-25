import pandas as pd
import pytest

from microalpha.evaluate import classification_metrics


def test_classification_metrics_known_example() -> None:
    frame = pd.DataFrame(
        {
            "horizon": [10, 10, 10],
            "model": ["m"] * 3,
            "y_true": [-1, 0, 1],
            "y_pred": [-1, 0, 1],
            "p_down": [1, 0, 0],
            "p_flat": [0, 1, 0],
            "p_up": [0, 0, 1],
        }
    )
    result = classification_metrics(frame)["h10_m"]
    assert result["macro_f1"] == pytest.approx(1)
    assert result["balanced_accuracy"] == pytest.approx(1)
    assert result["mcc"] == pytest.approx(1)
    assert result["multiclass_brier"] == pytest.approx(0)
    assert result["confusion_matrix"] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
