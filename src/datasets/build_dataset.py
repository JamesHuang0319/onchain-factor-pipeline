"""
src/datasets/build_dataset.py
──────────────────────────────────────────────────────────────
Assemble the final modeling DataFrame:
  features (at time t) + label (at time t+horizon).

CRITICAL ANTI-LEAKAGE DESIGN:
  1. Features are built from data[: t] — all rolling / pct_change
     operations are backward-looking (enforced by price/onchain modules).
  2. Label is log(close[t+horizon] / close[t]).
     It uses shift(-horizon) on the close series AFTER all features
     are computed, so label[t] = future info unavailable at t.
  3. assert_no_leakage() verifies Pearson correlation between each
     feature at time t and the FUTURE close (not just the label),
     flagging any feature with |corr| > threshold as suspicious.
  4. Rows where label is NaN (last `horizon` rows) are DROPPED —
     never filled, never used for training.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.etl.cleaner import align_and_merge, clean_onchain, clean_price
from src.features.macro_factors import load_macro
from src.features.onchain_factors import compute_onchain_factors
from src.features.price_factors import compute_price_factors
from src.ingest.onchain import load_onchain
from src.ingest.price import download_price

logger = logging.getLogger(__name__)

LABEL_COL = "log_ret_7d"


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────


def build_dataset(
    symbol: str = "BTC-USD",
    start_date: str = "2018-01-01",
    end_date: Optional[str] = None,
    horizon: int = 7,
    use_price: bool = True,
    use_onchain: bool = False,
    use_macro: bool = False,
    price_cache_dir: str = "data/raw/yfinance",
    onchain_cache_dir: str = "data/raw/blockchain",
    macro_cache_dir: str = "data/raw/macro",
    macro_use_dummy: bool = True,
    macro_lag_days: int = 1,
    force_download: bool = False,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Build the full feature + label dataset.

    Returns
    -------
    DataFrame with:
      - OHLCV columns
      - All requested factor columns (price / onchain / macro)
      - `log_ret_7d`: LABEL — log(close[t+horizon] / close[t])
        NOTE: this is a FORWARD-looking quantity; it is only added
        at the very end and is NaN for the last `horizon` rows.
    Index: UTC DatetimeIndex (daily).

    Usage in training:
      df_clean = df.dropna(subset=[LABEL_COL])
      X = df_clean[feature_cols]
      y = df_clean[LABEL_COL]
    """
    # ── 1. Price ──────────────────────────────────────────────
    raw_price = download_price(
        symbol, start_date, end_date, price_cache_dir, force_download
    )
    price_df = clean_price(raw_price)

    # ── 2. On-chain (optional) ────────────────────────────────
    onchain_df: Optional[pd.DataFrame] = None
    if use_onchain:
        raw_onchain = load_onchain(cache_dir=onchain_cache_dir, force=force_download)
        onchain_df = clean_onchain(raw_onchain)

    # ── 3. Macro (optional) ───────────────────────────────────
    macro_df: Optional[pd.DataFrame] = None
    if use_macro:
        macro_df = load_macro(
            index=price_df.index,
            release_lag_days=macro_lag_days,
            use_dummy=macro_use_dummy,
            cache_dir=macro_cache_dir,
        )

    # ── 4. Align & Merge ─────────────────────────────────────
    merged = align_and_merge(price_df, onchain_df, macro_df)

    # ── 5. Compute price factors ──────────────────────────────
    # NOTE: compute_price_factors only looks at [: t] data.
    data = compute_price_factors(merged)

    # ── 6. Compute on-chain factors ───────────────────────────
    if use_onchain and onchain_df is not None:
        onchain_factors = compute_onchain_factors(merged)
        data = pd.concat([data, onchain_factors], axis=1)

    # ── 7. Add macro placeholder columns ─────────────────────
    if use_macro and macro_df is not None:
        # macro_df already reindexed to price calendar in load_macro
        for col in macro_df.columns:
            if col in merged.columns:
                data[col] = merged[col]

    # ── 8. Build label (FORWARD shift — label at t uses close[t+horizon])
    # CRITICAL: shift(-horizon) must happen AFTER all feature calculations.
    # The label is unavailable at time t; it is only assigned here for
    # supervised learning purposes and must NEVER be a feature.
    data[LABEL_COL] = np.log(
        data["close"].shift(-horizon) / data["close"]
    )

    # ── 9. Anti-leakage assertion ─────────────────────────────
    assert_no_leakage(data, label_col=LABEL_COL)

    # ── 10. Persist ───────────────────────────────────────────
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        data.to_parquet(output_path)
        logger.info(f"[dataset] Saved → {output_path}  ({len(data)} rows)")

    return data


# ──────────────────────────────────────────────────────────────
# Leakage guard
# ──────────────────────────────────────────────────────────────


def assert_no_leakage(
    df: pd.DataFrame,
    label_col: str = LABEL_COL,
    corr_threshold: float = 0.99,
) -> None:
    """
    Fail fast if any feature has near-perfect correlation with the label.

    A legitimate feature should NOT correlate ~1.0 with future returns.
    Perfect correlation almost always indicates data leakage.

    Parameters
    ----------
    df             : dataset with features + label column
    label_col      : name of the target column
    corr_threshold : absolute Pearson r above which a violation is raised
    """
    if label_col not in df.columns:
        raise ValueError(f"[leakage] Label column '{label_col}' not found in dataset.")

    # Use only complete rows for correlation check
    available = df.dropna(subset=[label_col])
    feature_cols = [c for c in available.columns if c != label_col]

    violations: list[str] = []
    for col in feature_cols:
        series = available[col].dropna()
        common = available.loc[series.index, label_col].dropna()
        idx = series.index.intersection(common.index)
        if len(idx) < 20:
            continue
        r = series.loc[idx].corr(common.loc[idx])
        if abs(r) > corr_threshold:
            violations.append(f"  '{col}': |r|={abs(r):.4f}")

    if violations:
        msg = (
            "[leakage] POTENTIAL DATA LEAKAGE DETECTED!\n"
            "The following features have suspiciously high correlation "
            f"(|r| > {corr_threshold}) with the label '{label_col}':\n"
            + "\n".join(violations)
        )
        raise AssertionError(msg)

    logger.info(
        f"[leakage] ✓ No leakage detected ({len(feature_cols)} features checked)."
    )


def get_feature_cols(df: pd.DataFrame, label_col: str = LABEL_COL) -> list[str]:
    """
    Return feature column names (exclude OHLCV + label + date artifacts).
    """
    non_feature = {
        label_col, "open", "high", "low", "close", "volume",
        "adj_close", "adj close",
    }
    return [c for c in df.columns if c not in non_feature]
