from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from src.models.base import BaseModel


class RFModel(BaseModel):
    """
    Task-aware Random Forest wrapper.
    - classification -> RandomForestClassifier
    - regression     -> RandomForestRegressor
    """

    name = "rf"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        task = str(self.config.get("task", "regression")).lower()
        common = dict(
            n_estimators=int(self.config.get("n_estimators", 500)),
            max_depth=self.config.get("max_depth", None),
            min_samples_split=int(self.config.get("min_samples_split", 2)),
            min_samples_leaf=int(self.config.get("min_samples_leaf", 1)),
            max_features=self.config.get("max_features", "sqrt"),
            random_state=int(self.config.get("random_state", 42)),
            n_jobs=int(self.config.get("n_jobs", -1)),
        )
        if task == "classification":
            self._model = RandomForestClassifier(
                class_weight=self.config.get("class_weight", "balanced"),
                **common,
            )
        else:
            self._model = RandomForestRegressor(**common)

    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "RFModel":
        _ = (X_val, y_val)
        self._model.fit(X_train, y_train)
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        task = str(self.config.get("task", "regression")).lower()
        if task == "classification" and hasattr(self._model, "predict_proba"):
            return self._model.predict_proba(X)[:, 1].astype(float)
        return self._model.predict(X).astype(float)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"model": self._model, "config": self.config}, f)

    @classmethod
    def load(cls, path: str | Path) -> "RFModel":
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(config=data["config"])
        obj._model = data["model"]
        return obj

