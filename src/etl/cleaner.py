"""
src/etl/cleaner.py
──────────────────────────────────────────────────────────────
Clean, align, and merge raw data into daily UTC panels.

Key rules (anti-leakage):
  1. All operations are purely backward-looking (no future data).
  2. Forward-fill on-chain / macro data (last-known-value, safe).
  3. Missing price rows are DROPPED (not forward-filled) to avoid
     spurious signals on non-trading days.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def clean_price(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a single-asset OHLCV DataFrame returned by ingest.price.

    - Drop rows where close == 0 or close is NaN
    - Ensure UTC DatetimeIndex
    - Rename columns to lowercase
    - Sort ascending
    """
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    # Ensure UTC
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df.index = df.index.normalize()
    df.index.name = "date"

    df = df.sort_index()

    # Drop rows with invalid close
    invalid_mask = df["close"].isna() | (df["close"] <= 0)
    n_dropped = invalid_mask.sum()
    if n_dropped:
        logger.warning(f"[etl] Dropping {n_dropped} rows with invalid close price.")
    df = df[~invalid_mask]

    # Drop fully-duplicate dates (keep last)
    df = df[~df.index.duplicated(keep="last")]
    return df


def clean_onchain(df: pd.DataFrame, ffill_limit: int = 7) -> pd.DataFrame:
    """
    Clean a merged on-chain DataFrame.

    - Forward-fill gaps up to `ffill_limit` days (safe: uses past data)
    - Log-transform non-negative metrics (avoids scale issues)
    """
    df = df.copy()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.normalize()
    df.index.name = "date"
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]

    # Forward-fill (backward is forbidden – it uses future data!)
    df = df.ffill(limit=ffill_limit)
    return df


def align_and_merge(
    price_df: pd.DataFrame,
    onchain_df: Optional[pd.DataFrame] = None,
    macro_df: Optional[pd.DataFrame] = None,
    ffill_onchain: int = 7,
    ffill_macro: int = 30,
) -> pd.DataFrame:
    """
    Merge price, on-chain, and macro onto the price calendar (inner join on
    price dates). On-chain/macro columns are forward-filled so the value at
    date t is the last-known value at or before t.

    Parameters
    ----------
    price_df    : cleaned OHLCV DataFrame (price calendar is the master)
    onchain_df  : cleaned on-chain DataFrame (optional)
    macro_df    : cleaned macro DataFrame (optional)
    ffill_onchain / ffill_macro : max consecutive days to forward-fill

    Returns
    -------
    Merged DataFrame indexed by price dates (UTC).
    """
    merged = price_df.copy()

    if onchain_df is not None:
        # Reindex to price calendar, forward-fill (safe: only past data)
        onchain_aligned = (
            onchain_df
            .reindex(merged.index, method="ffill")
            .ffill(limit=ffill_onchain)
        )
        merged = pd.concat([merged, onchain_aligned], axis=1)

    if macro_df is not None:
        macro_aligned = (
            macro_df
            .reindex(merged.index, method="ffill")
            .ffill(limit=ffill_macro)
        )
        merged = pd.concat([merged, macro_aligned], axis=1)

    # After merging, drop rows where price columns are NaN
    price_cols = ["open", "high", "low", "close", "volume"]
    existing_price_cols = [c for c in price_cols if c in merged.columns]
    merged = merged.dropna(subset=existing_price_cols, how="any")

    logger.info(
        f"[etl] Merged DataFrame: {len(merged)} rows, "
        f"{merged.shape[1]} columns, "
        f"{merged.index[0].date()} → {merged.index[-1].date()}"
    )
    return merged
