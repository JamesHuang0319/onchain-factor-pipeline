"""
src/models/ridge.py
──────────────────────────────────────────────────────────────
Ridge regression model wrapping sklearn.
Includes optional StandardScaler (recommended for Ridge).
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.models.base import BaseModel


class RidgeModel(BaseModel):
    """Ridge regression with optional feature scaling."""

    name = "ridge"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        alpha = float(self.config.get("alpha", 1.0))
        fit_intercept = bool(self.config.get("fit_intercept", True))
        normalize = bool(self.config.get("normalize_features", True))

        steps: list = []
        if normalize:
            steps.append(("scaler", StandardScaler()))
        steps.append(("ridge", Ridge(alpha=alpha, fit_intercept=fit_intercept)))
        self._pipeline = Pipeline(steps)

    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "RidgeModel":
        # Ridge does not use validation data (no early stopping)
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
            pickle.dump(self._pipeline, f)

    @classmethod
    def load(cls, path: str | Path) -> "RidgeModel":
        obj = cls()
        with open(path, "rb") as f:
            obj._pipeline = pickle.load(f)
        obj._model = obj._pipeline
        return obj
