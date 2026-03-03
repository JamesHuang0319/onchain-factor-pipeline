"""
src/models/base.py
──────────────────────────────────────────────────────────────
Abstract base class for all models.
Concrete subclasses must implement: fit / predict / save / load.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


class BaseModel(ABC):
    """Unified interface for all prediction models."""

    name: str = "base"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}
        self._model: Any = None  # underlying sklearn / lgbm / xgb model

    # ── Abstract methods ──────────────────────────────────────

    @abstractmethod
    def fit(
        self,
        X_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: pd.Series | np.ndarray | None = None,
    ) -> "BaseModel":
        """Train the model. Must return self."""
        ...

    @abstractmethod
    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Return predicted values (regression)."""
        ...

    @abstractmethod
    def save(self, path: str | Path) -> None:
        """Persist the trained model to disk."""
        ...

    @classmethod
    @abstractmethod
    def load(cls, path: str | Path) -> "BaseModel":
        """Load a persisted model from disk."""
        ...

    # ── Convenience helpers ───────────────────────────────────

    def fit_predict(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
    ) -> np.ndarray:
        """Train and return test predictions in one call."""
        self.fit(X_train, y_train)
        return self.predict(X_test)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"
