"""
src/features/onchain_factors.py
──────────────────────────────────────────────────────────────
Build on-chain derived factors from raw Blockchain.com metrics.

ANTI-LEAKAGE: all operations use only data[: t] (rolling window,
pct_change, shift). No future information.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_onchain_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive 10+ on-chain factors from raw blockchain metrics.

    Input
    -----
    df : DataFrame with columns such as:
         n-transactions, n-unique-addresses, hash-rate, difficulty
         UTC DatetimeIndex (already aligned to price calendar via ETL)

    Returns
    -------
    DataFrame containing ONLY the derived factor columns (no raw cols).
    Caller merges this with the price factor DataFrame.
    """
    out = pd.DataFrame(index=df.index)

    def _safe_col(name: str) -> pd.Series | None:
        """Return column Series or None if not present."""
        return df[name] if name in df.columns else None

    # ── n-transactions ──────────────────────────────────────
    ntx = _safe_col("n-transactions")
    if ntx is not None:
        out["ntx_pct_1d"]   = ntx.pct_change(1)
        out["ntx_pct_7d"]   = ntx.pct_change(7)
        out["ntx_ma7_dev"]  = ntx / ntx.rolling(7,  min_periods=4).mean() - 1
        out["ntx_ma30_dev"] = ntx / ntx.rolling(30, min_periods=15).mean() - 1

    # ── n-unique-addresses ──────────────────────────────────
    addr = _safe_col("n-unique-addresses")
    if addr is not None:
        out["addr_pct_1d"]  = addr.pct_change(1)
        out["addr_pct_7d"]  = addr.pct_change(7)
        out["addr_ma7_dev"] = addr / addr.rolling(7, min_periods=4).mean() - 1

    # ── hash-rate ───────────────────────────────────────────
    hr = _safe_col("hash-rate")
    if hr is not None:
        out["hashrate_pct_7d"]   = hr.pct_change(7)
        out["hashrate_ma14_dev"] = hr / hr.rolling(14, min_periods=7).mean() - 1

    # ── difficulty ──────────────────────────────────────────
    diff = _safe_col("difficulty")
    if diff is not None:
        out["diff_pct_14d"]    = diff.pct_change(14)
        out["diff_ma30_dev"]   = diff / diff.rolling(30, min_periods=15).mean() - 1

    # ── Cross-metric: miner revenue proxy ───────────────────
    # hash-rate / difficulty indicates miner efficiency signal
    if hr is not None and diff is not None:
        # Avoid division by zero
        out["hr_diff_ratio"] = hr / diff.replace(0, np.nan)
        out["hr_diff_pct_7d"] = out["hr_diff_ratio"].pct_change(7)

    return out
