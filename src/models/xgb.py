"""
src/models/xgb.py
──────────────────────────────────────────────────────────────
Standalone XGBoost model wrapper.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.models.base import BaseModel


class XGBoostModel(BaseModel):
    """Native XGBoost wrapper for classification and regression."""

    name = "xgboost"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        import xgboost as xgb

        task = str(self.config.get("task", "regression")).lower()
        common = dict(
            n_estimators=int(self.config.get("n_estimators", 500)),
            learning_rate=float(self.config.get("learning_rate", 0.03)),
            max_depth=int(self.config.get("max_depth", 6)),
            subsample=float(self.config.get("subsample", 0.8)),
            colsample_bytree=float(self.config.get("colsample_bytree", 0.8)),
            reg_alpha=float(self.config.get("reg_alpha", 0.0)),
            reg_lambda=float(self.config.get("reg_lambda", 1.0)),
            random_state=int(self.config.get("random_state", 42)),
            n_jobs=int(self.config.get("n_jobs", -1)),
            verbosity=0,
        )

        if task == "classification":
            self._model = xgb.XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                **common,
            )
        else:
            self._model = xgb.XGBRegressor(
                objective="reg:squarederror",
                eval_metric="rmse",
                **common,
            )

    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "XGBoostModel":
        if X_val is not None and y_val is not None:
            self._model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        else:
            self._model.fit(X_train, y_train)
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        task = str(self.config.get("task", "regression")).lower()
        if task == "classification":
            return self._model.predict_proba(X)[:, 1].astype(float)
        return self._model.predict(X).astype(float)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"model": self._model, "config": self.config}, f)

    @classmethod
    def load(cls, path: str | Path) -> "XGBoostModel":
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(config=data["config"])
        obj._model = data["model"]
        return obj
