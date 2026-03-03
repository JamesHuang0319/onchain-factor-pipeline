"""
src/features/price_factors.py
──────────────────────────────────────────────────────────────
Compute 20+ price-based factors from OHLCV data.

ANTI-LEAKAGE RULES enforced here:
  - All rolling/shift operations use only past data (min_periods set).
  - No look-ahead window (window=N means last N bars including current).
  - The label column is NOT built here; it's added in build_dataset.py
    via a FORWARD shift, strictly after the feature matrix is final.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Wilder RSI — uses only past data (no future)."""
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_price_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build price-only factor matrix.

    Input
    -----
    df : cleaned OHLCV DataFrame (UTC DatetimeIndex)
         Required columns: open, high, low, close, volume

    Returns
    -------
    DataFrame with all original OHLCV columns PLUS factor columns.
    Rows with insufficient history (leading NaNs) are kept — callers
    may dropna() after combining all factor groups.
    """
    out = df.copy()
    c = out["close"]
    h = out["high"]
    lo = out["low"]
    v = out["volume"]

    # ── 1. Momentum (log returns) ────────────────────────────
    # log(close_t / close_{t-k}) — purely backward-looking
    for k in [1, 7, 14, 30]:
        out[f"mom_{k}d"] = np.log(c / c.shift(k))

    # ── 2. Realised Volatility (rolling std of log returns) ──
    log_ret = np.log(c / c.shift(1))
    for w in [7, 14, 30]:
        out[f"vol_{w}d"] = log_ret.rolling(w, min_periods=w // 2).std()

    # ── 3. Volume change rate ────────────────────────────────
    out["vol_pct_1d"] = v.pct_change()
    out["vol_pct_7d"] = v.pct_change(7)
    # Volume vs. 30-day MA (normalised)
    out["vol_ma30_ratio"] = v / v.rolling(30, min_periods=15).mean()

    # ── 4. MA deviation (close / MA - 1) ────────────────────
    for w in [7, 20, 60]:
        ma = c.rolling(w, min_periods=w // 2).mean()
        out[f"ma{w}_dev"] = c / ma - 1

    # ── 5. Amplitude (intraday range / close) ───────────────
    out["amplitude"] = (h - lo) / c

    # ── 6. High-Low range vs. N-day range ───────────────────
    out["hl_range_7d"] = (h.rolling(7).max() - lo.rolling(7).min()) / c

    # ── 7. RSI ───────────────────────────────────────────────
    out["rsi_14"] = _rsi(c, window=14)

    # ── 8. MACD-like: fast - slow EMA (normalised) ──────────
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    out["macd_norm"] = (ema12 - ema26) / c

    # ── 9. Price position within N-day range (William %R) ───
    for w in [14, 30]:
        h_max = h.rolling(w, min_periods=w // 2).max()
        lo_min = lo.rolling(w, min_periods=w // 2).min()
        out[f"williams_r_{w}d"] = (h_max - c) / (h_max - lo_min + 1e-9)

    # ── 10. Close vs. open (intraday body) ──────────────────
    out["close_open_ret"] = np.log(c / out["open"])

    return out
