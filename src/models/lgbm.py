"""
src/models/lgbm.py
──────────────────────────────────────────────────────────────
Gradient-boosting model with fallback chain:
  LightGBM → XGBoost → sklearn HistGradientBoostingRegressor

All seeds fixed via config["random_state"].
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.models.base import BaseModel

logger = logging.getLogger(__name__)


def _build_gbm(config: dict[str, Any]):
    """Instantiate the best available GBM with given config."""
    rs = int(config.get("random_state", 42))
    n_est = int(config.get("n_estimators", 300))
    lr = float(config.get("learning_rate", 0.05))
    max_d = int(config.get("max_depth", 4))
    n_jobs = int(config.get("n_jobs", -1))

    # ── Try LightGBM first ────────────────────────────────────
    try:
        import lightgbm as lgb
        model = lgb.LGBMRegressor(
            n_estimators=n_est,
            learning_rate=lr,
            max_depth=max_d,
            num_leaves=int(config.get("num_leaves", 31)),
            min_child_samples=int(config.get("min_child_samples", 20)),
            subsample=float(config.get("subsample", 0.8)),
            colsample_bytree=float(config.get("colsample_bytree", 0.8)),
            reg_alpha=float(config.get("reg_alpha", 0.1)),
            reg_lambda=float(config.get("reg_lambda", 1.0)),
            random_state=rs,
            n_jobs=n_jobs,
            verbose=-1,
        )
        logger.info("[lgbm] Using LightGBM backend.")
        return model, "lightgbm"
    except ImportError:
        logger.warning("[lgbm] LightGBM not found, trying XGBoost …")

    # ── Fallback 1: XGBoost ───────────────────────────────────
    try:
        import xgboost as xgb
        model = xgb.XGBRegressor(
            n_estimators=n_est,
            learning_rate=lr,
            max_depth=max_d,
            subsample=float(config.get("subsample", 0.8)),
            colsample_bytree=float(config.get("colsample_bytree", 0.8)),
            reg_alpha=float(config.get("reg_alpha", 0.1)),
            reg_lambda=float(config.get("reg_lambda", 1.0)),
            random_state=rs,
            n_jobs=n_jobs,
            verbosity=0,
        )
        logger.info("[lgbm] Using XGBoost backend.")
        return model, "xgboost"
    except ImportError:
        logger.warning("[lgbm] XGBoost not found, falling back to sklearn HGBR …")

    # ── Fallback 2: sklearn HistGradientBoostingRegressor ─────
    from sklearn.ensemble import HistGradientBoostingRegressor
    model = HistGradientBoostingRegressor(
        max_iter=n_est,
        learning_rate=lr,
        max_depth=max_d,
        random_state=rs,
    )
    logger.info("[lgbm] Using sklearn HistGradientBoostingRegressor backend.")
    return model, "hgbr"


class GBMModel(BaseModel):
    """Gradient-boosting model with LightGBM/XGBoost/HGBR fallback."""

    name = "gbm"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._model, self.backend = _build_gbm(self.config)

    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "GBMModel":
        if self.backend == "lightgbm" and X_val is not None:
            # LightGBM early stopping with validation set
            import lightgbm as lgb
            self._model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                callbacks=[lgb.early_stopping(50, verbose=False),
                           lgb.log_evaluation(period=-1)],
            )
        elif self.backend == "xgboost" and X_val is not None:
            self._model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
        else:
            self._model.fit(X_train, y_train)
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self._model.predict(X).astype(float)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"model": self._model, "backend": self.backend,
                         "config": self.config}, f)

    @classmethod
    def load(cls, path: str | Path) -> "GBMModel":
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(config=data["config"])
        obj._model = data["model"]
        obj.backend = data["backend"]
        return obj
