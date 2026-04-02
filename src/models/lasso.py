from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.models.base import BaseModel


class LassoModel(BaseModel):
    """Lasso regression wrapper with optional feature scaling."""

    name = "lasso"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        alpha = float(self.config.get("alpha", 0.001))
        max_iter = int(self.config.get("max_iter", 5000))
        tol = float(self.config.get("tol", 1e-4))
        normalize = bool(self.config.get("normalize_features", True))
        random_state = int(self.config.get("random_state", 42))

        steps: list[tuple[str, Any]] = []
        if normalize:
            steps.append(("scaler", StandardScaler()))
        steps.append(
            (
                "lasso",
                Lasso(alpha=alpha, max_iter=max_iter, tol=tol, random_state=random_state),
            )
        )
        self._pipeline = Pipeline(steps)

    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "LassoModel":
        _ = (X_val, y_val)
        self._pipeline.fit(X_train, y_train)
        self._model = self._pipeline
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        return self._model.predict(X).astype(float)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"pipeline": self._pipeline, "config": self.config}, f)

    @classmethod
    def load(cls, path: str | Path) -> "LassoModel":
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(config=data["config"])
        obj._pipeline = data["pipeline"]
        obj._model = obj._pipeline
        return obj

