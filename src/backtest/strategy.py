"""
src/backtest/strategy.py
──────────────────────────────────────────────────────────────
Convert model predictions into daily position weights.

Strategy modes
──────────────
long_only   : weight = 1.0 if pred > 0, else 0.0  (single-asset)
long_short  : cross-sectional rank bucketing        (multi-asset)
              top-Q% → +1 / bottom-Q% → -1 / rest → 0

ANTI-LOOKAHEAD: trade signal on day t uses prediction made with
data available AT CLOSE of day t.  Actual entry is the OPEN of
day t+1 (simulated via next_open = open.shift(-1)).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def long_only_signal(
    predictions: pd.Series,
    top_quantile: float = 1.0,      # 1.0 means any positive prediction
) -> pd.Series:
    """
    Single-asset long-only rule.

    Parameters
    ----------
    predictions  : Series of predicted 7-day log returns, DatetimeIndex.
    top_quantile : only go long when prediction is in the top quantile.
                   Default 1.0 → go long whenever pred > 0.

    Returns
    -------
    Signal Series: 1.0 (long) or 0.0 (flat).
    Values represent POSITION on day t (entered at open of t+1).
    """
    if top_quantile < 1.0:
        threshold = predictions.quantile(1 - top_quantile)
        return (predictions >= threshold).astype(float)
    else:
        return (predictions > 0).astype(float)


def long_short_signal(
    predictions: pd.Series,
    top_quantile: float = 0.2,
    bottom_quantile: float = 0.2,
) -> pd.Series:
    """
    Long/Short cross-sectional ranking signal.

    Returns
    -------
    Signal Series: +1 (long) / -1 (short) / 0 (flat).
    """
    signal = pd.Series(0.0, index=predictions.index)
    signal[predictions >= predictions.quantile(1 - top_quantile)]    = 1.0
    signal[predictions <= predictions.quantile(bottom_quantile)]      = -1.0
    return signal


def make_signal(
    predictions: pd.Series,
    mode: str = "long_only",
    top_quantile: float = 0.2,
    bottom_quantile: float = 0.2,
) -> pd.Series:
    """
    Dispatch to the correct signal generator.

    Parameters
    ----------
    predictions     : model output Series (DatetimeIndex daily)
    mode            : "long_only" or "long_short"
    top_quantile    : fraction for long book
    bottom_quantile : fraction for short book

    Returns
    -------
    Signal Series aligned to predictions.index.
    """
    if mode == "long_short":
        return long_short_signal(predictions, top_quantile, bottom_quantile)
    else:
        # "long_only" — go long whenever prediction is positive
        return long_only_signal(predictions, top_quantile=1.0)
