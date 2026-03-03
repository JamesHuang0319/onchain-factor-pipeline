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
    out.index = pd.to_datetime(out.index, utc=True).normalize()

    metric_prefix = {
        "n-transactions": "ntx",
        "n-unique-addresses": "addr",
        "transaction-fees": "fees",
        "estimated-transaction-volume": "txvol",
        "mempool-size": "mempool",
        "miners-revenue": "mrev",
        "cost-per-transaction": "cptx",
        "hash-rate": "hr",
        "difficulty": "diff",
    }

    def _zscore(x: pd.Series, window: int, min_periods: int) -> pd.Series:
        mean = x.rolling(window, min_periods=min_periods).mean()
        std = x.rolling(window, min_periods=min_periods).std()
        return (x - mean) / std.replace(0, np.nan)

    for metric, prefix in metric_prefix.items():
        if metric not in df.columns:
            continue
        s = pd.to_numeric(df[metric], errors="coerce")
        s_pos = s.clip(lower=0)
        ma7 = s.rolling(7, min_periods=4).mean().replace(0, np.nan)

        out[f"{prefix}_log1p"] = np.log1p(s_pos)
        out[f"{prefix}_pct_1d"] = s.pct_change(1)
        out[f"{prefix}_pct_7d"] = s.pct_change(7)
        out[f"{prefix}_ma7_dev"] = s / ma7 - 1
        out[f"{prefix}_z30"] = _zscore(s, window=30, min_periods=15)

    ntx = df["n-transactions"] if "n-transactions" in df.columns else None
    addr = df["n-unique-addresses"] if "n-unique-addresses" in df.columns else None
    fees = df["transaction-fees"] if "transaction-fees" in df.columns else None
    txvol = (
        df["estimated-transaction-volume"]
        if "estimated-transaction-volume" in df.columns
        else None
    )
    mrev = df["miners-revenue"] if "miners-revenue" in df.columns else None
    hr = df["hash-rate"] if "hash-rate" in df.columns else None
    diff = df["difficulty"] if "difficulty" in df.columns else None

    if ntx is not None and addr is not None:
        out["tx_per_addr"] = ntx / addr.replace(0, np.nan)
        out["tx_per_addr_pct_7d"] = out["tx_per_addr"].pct_change(7)
    if fees is not None and ntx is not None:
        out["fees_per_tx"] = fees / ntx.replace(0, np.nan)
        out["fees_per_tx_z30"] = _zscore(out["fees_per_tx"], window=30, min_periods=15)
    if txvol is not None and fees is not None:
        out["fees_txvol_ratio"] = fees / txvol.replace(0, np.nan)
    if mrev is not None and hr is not None:
        out["mrev_per_hash"] = mrev / hr.replace(0, np.nan)
    if hr is not None and diff is not None:
        out["hr_diff_ratio"] = hr / diff.replace(0, np.nan)
        out["hr_diff_ratio_pct_7d"] = out["hr_diff_ratio"].pct_change(7)

    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out
