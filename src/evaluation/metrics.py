"""
src/evaluation/metrics.py
──────────────────────────────────────────────────────────────
Regression evaluation metrics for forecasting quality.

Metrics:
  - MAE   : Mean Absolute Error
  - MSE   : Mean Squared Error
  - RMSE  : Root MSE
  - RankIC: Pearson correlation between rank(y_pred) and rank(y_true)
            a.k.a. Spearman correlation — measures directional quality
  - IC    : Information Coefficient (Pearson of y_pred vs y_true)
  - ICIR  : IC / std(IC)  — measured across rolling windows
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean((y_true - y_pred) ** 2))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mse(y_true, y_pred)))


def ic(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Pearson IC between predictions and realized returns."""
    if len(y_true) < 2:
        return float("nan")
    r, _ = stats.pearsonr(y_pred, y_true)
    return float(r)


def rank_ic(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    RankIC = Spearman rank correlation between predictions and returns.
    More robust than Pearson IC to outliers.
    """
    if len(y_true) < 2:
        return float("nan")
    r, _ = stats.spearmanr(y_pred, y_true)
    return float(r)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    prefix: str = "",
) -> dict[str, float]:
    """Compute all regression metrics and return as dict."""
    p = f"{prefix}_" if prefix else ""
    return {
        f"{p}mae":     mae(y_true, y_pred),
        f"{p}mse":     mse(y_true, y_pred),
        f"{p}rmse":    rmse(y_true, y_pred),
        f"{p}ic":      ic(y_true, y_pred),
        f"{p}rank_ic": rank_ic(y_true, y_pred),
    }


def rolling_icir(
    y_true: pd.Series,
    y_pred: pd.Series,
    window: int = 12,
) -> float:
    """
    ICIR = mean(rolling_IC) / std(rolling_IC).
    Measures consistency of prediction skill over time.
    """
    ics: list[float] = []
    dates = y_true.index
    for i in range(window, len(dates) + 1):
        yt = y_true.iloc[i - window: i].values
        yp = y_pred.iloc[i - window: i].values
        ics.append(ic(yt, yp))
    ics_arr = np.array(ics)
    std = np.nanstd(ics_arr)
    if std == 0:
        return float("nan")
    return float(np.nanmean(ics_arr) / std)
