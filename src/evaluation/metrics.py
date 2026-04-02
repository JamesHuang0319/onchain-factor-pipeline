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


def oos_r2(y_true: np.ndarray, y_pred: np.ndarray, benchmark: np.ndarray) -> float:
    """
    Out-of-sample R^2 against a benchmark prediction.

    OOS_R2 = 1 - SSE_model / SSE_benchmark
    """
    if len(y_true) == 0:
        return float("nan")
    sse_model = float(np.sum((y_true - y_pred) ** 2))
    sse_bench = float(np.sum((y_true - benchmark) ** 2))
    if sse_bench == 0:
        return float("nan")
    return float(1.0 - sse_model / sse_bench)


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


def compute_classification_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    prefix: str = "",
    threshold: float = 0.5,
) -> dict[str, float]:
    """
    Compute binary classification metrics from score/probability predictions.
    """
    y_true_bin = np.asarray(y_true).astype(int)
    y_pred_bin = (np.asarray(y_score) >= float(threshold)).astype(int)
    p = f"{prefix}_" if prefix else ""

    tp = float(np.sum((y_true_bin == 1) & (y_pred_bin == 1)))
    tn = float(np.sum((y_true_bin == 0) & (y_pred_bin == 0)))
    fp = float(np.sum((y_true_bin == 0) & (y_pred_bin == 1)))
    fn = float(np.sum((y_true_bin == 1) & (y_pred_bin == 0)))
    n = max(1.0, tp + tn + fp + fn)

    accuracy = (tp + tn) / n
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {
        f"{p}accuracy": float(accuracy),
        f"{p}precision": float(precision),
        f"{p}recall": float(recall),
        f"{p}f1": float(f1),
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
