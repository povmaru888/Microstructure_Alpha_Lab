"""Leakage-controlled model training utilities."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CLASSES = np.array([-1, 0, 1], dtype=np.int8)


@dataclass
class Preprocessor:
    feature_order: tuple[str, ...]
    dtypes: dict[str, str]
    pipeline: Pipeline
    fitted_split: str = "train"

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        return self.pipeline.transform(frame.loc[:, self.feature_order])


def fit_preprocessor(train: pd.DataFrame, feature_order: list[str]) -> Preprocessor:
    pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    pipeline.fit(train.loc[:, feature_order])
    return Preprocessor(
        tuple(feature_order), {name: str(train[name].dtype) for name in feature_order}, pipeline
    )


def train_majority(y_train: pd.Series) -> dict:
    counts = y_train.value_counts()
    majority = int(sorted(counts[counts == counts.max()].index)[0])
    return {"model_type": "majority", "majority_class": majority, "classes": CLASSES.tolist()}


def predict_majority(model: dict, count: int) -> tuple[np.ndarray, np.ndarray]:
    predictions = np.full(count, model["majority_class"], dtype=np.int8)
    probabilities = np.zeros((count, 3))
    probabilities[:, list(CLASSES).index(model["majority_class"])] = 1.0
    return predictions, probabilities


def fit_obi_rule(
    train: pd.DataFrame, valid: pd.DataFrame, candidates: tuple[float, ...] = (0.1, 0.2, 0.3)
) -> dict:
    from sklearn.metrics import f1_score

    best = None
    for threshold in candidates:
        prediction = np.where(
            valid["obi_l1"] > threshold, 1, np.where(valid["obi_l1"] < -threshold, -1, 0)
        )
        score = f1_score(
            valid["label"], prediction, average="macro", labels=CLASSES, zero_division=0
        )
        candidate = (score, -threshold, threshold)
        if best is None or candidate > best:
            best = candidate
    assert best
    return {"model_type": "obi_rule", "threshold": best[2], "selected_using": ["train", "valid"]}


def train_logistic(train: pd.DataFrame, features: list[str], random_state: int = 42) -> Pipeline:
    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, random_state=random_state)),
        ]
    )
    return model.fit(train[features], train["label"])


def train_xgboost(
    train: pd.DataFrame, valid: pd.DataFrame, features: list[str], random_state: int = 42
) -> tuple[object, dict]:
    from sklearn.metrics import log_loss
    from xgboost import XGBClassifier

    mapping = {-1: 0, 0: 1, 1: 2}
    best = None
    for depth in (2, 3):
        model = XGBClassifier(
            n_estimators=30,
            max_depth=depth,
            learning_rate=0.1,
            objective="multi:softprob",
            num_class=3,
            random_state=random_state,
            n_jobs=1,
            early_stopping_rounds=5,
        )
        model.fit(
            train[features],
            train["label"].map(mapping),
            eval_set=[(valid[features], valid["label"].map(mapping))],
            verbose=False,
        )
        loss = log_loss(
            valid["label"].map(mapping), model.predict_proba(valid[features]), labels=[0, 1, 2]
        )
        if best is None or loss < best[0]:
            best = (loss, model, depth)
    assert best
    return best[1], {
        "model_type": "xgboost",
        "max_depth": best[2],
        "random_state": random_state,
        "selected_using": "validation",
        "validation_log_loss": best[0],
        "early_stopping_rounds": 5,
        "best_iteration": int(best[1].best_iteration),
    }
