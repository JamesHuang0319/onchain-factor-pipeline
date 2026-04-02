from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR

from src.models.base import BaseModel


class SVMModel(BaseModel):
    """
    Task-aware SVM wrapper.
    - classification -> SVC(probability=True)
    - regression     -> SVR
    """

    name = "svm"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        task = str(self.config.get("task", "regression")).lower()
        use_scaler = bool(self.config.get("normalize_features", True))

        steps: list[tuple[str, Any]] = []
        if use_scaler:
            steps.append(("scaler", StandardScaler()))

        if task == "classification":
            model = SVC(
                C=float(self.config.get("C", 1.0)),
                kernel=str(self.config.get("kernel", "rbf")),
                gamma=self.config.get("gamma", "scale"),
                class_weight=self.config.get("class_weight", "balanced"),
                probability=bool(self.config.get("probability", True)),
                random_state=int(self.config.get("random_state", 42)),
            )
        else:
            model = SVR(
                C=float(self.config.get("C", 10.0)),
                kernel=str(self.config.get("kernel", "rbf")),
                gamma=self.config.get("gamma", "scale"),
                epsilon=float(self.config.get("epsilon", 0.01)),
            )

        steps.append(("svm", model))
        self._pipeline = Pipeline(steps)

    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "SVMModel":
        _ = (X_val, y_val)
        self._pipeline.fit(X_train, y_train)
        self._model = self._pipeline
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        task = str(self.config.get("task", "regression")).lower()
        if task == "classification":
            clf = self._model.named_steps["svm"]
            if hasattr(clf, "predict_proba"):
                return self._model.predict_proba(X)[:, 1].astype(float)
            pred = self._model.predict(X)
            return pred.astype(float)
        return self._model.predict(X).astype(float)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"pipeline": self._pipeline, "config": self.config}, f)

    @classmethod
    def load(cls, path: str | Path) -> "SVMModel":
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(config=data["config"])
        obj._pipeline = data["pipeline"]
        obj._model = obj._pipeline
        return obj

