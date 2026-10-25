import numpy as np
import pandas as pd

from microalpha.evaluate import build_test_predictions


def test_fixed_prediction_schema_and_common_test_ids() -> None:
    joined = pd.DataFrame(
        {
            "dataset_id": ["d"] * 3,
            "event_index": [7, 8, 9],
            "research_index": [7, 8, 9],
            "horizon": [10] * 3,
            "label": [-1, 0, 1],
            "split": ["test"] * 3,
            "obi_l1": [-0.5, 0, 0.5],
        }
    )
    models = {"h10_majority": {"majority_class": 0}, "h10_obi_rule": {"threshold": 0.2}}

    class Dummy:
        def predict(self, frame):
            return np.array([-1, 0, 1])

        def predict_proba(self, frame):
            return np.eye(3)

    models.update({"h10_logistic": Dummy(), "h10_xgboost": Dummy()})
    metadata = {"h10_logistic": {"features": ["obi_l1"]}, "h10_xgboost": {"features": ["obi_l1"]}}
    result = build_test_predictions(models, joined, metadata)
    assert {"y_true", "y_pred", "p_down", "p_flat", "p_up", "split"} <= set(result)
    assert all(group["event_index"].tolist() == [7, 8, 9] for _, group in result.groupby("model"))
    assert np.allclose(result[["p_down", "p_flat", "p_up"]].sum(axis=1), 1)
