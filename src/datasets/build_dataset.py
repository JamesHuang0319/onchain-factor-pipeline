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
from src.ingest.coinmetrics import load_coinmetrics
from src.ingest.glassnode import load_glassnode
from src.ingest.onchain import load_onchain
from src.ingest.price import download_price

logger = logging.getLogger(__name__)

LABEL_COL = "log_ret_h"
DIRECTION_LABEL_COL = "direction_h"


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────


def build_dataset(
    symbol: str = "BTC-USD",
    start_date: str = "2018-01-01",
    end_date: Optional[str] = None,
    horizon: int = 7,
    label_horizon_days: Optional[int] = None,
    use_price: bool = True,
    use_onchain: bool = False,
    use_macro: bool = False,
    onchain_provider: str = "blockchain",
    onchain_metrics: Optional[list[dict | str]] = None,
    onchain_timespan: str = "all",
    price_cache_dir: str = "data/raw/yfinance",
    onchain_cache_dir: str = "data/raw/blockchain",
    coinmetrics_cache_dir: str = "data/raw/coinmetrics",
    coinmetrics_asset: str = "btc",
    coinmetrics_frequency: str = "1d",
    coinmetrics_start_time: Optional[str] = None,
    coinmetrics_end_time: Optional[str] = None,
    glassnode_cache_dir: str = "data/raw/glassnode",
    use_glassnode: bool = False,
    glassnode_metrics: Optional[list[dict | str]] = None,
    glassnode_api_key_env: str = "GLASSNODE_API_KEY",
    glassnode_asset: str = "BTC",
    glassnode_interval: str = "24h",
    macro_cache_dir: str = "data/raw/macro",
    macro_use_dummy: bool = True,
    macro_lag_days: int = 1,
    force_download: bool = False,
    output_path: Optional[str] = None,
    drop_label_na: bool = True,
) -> pd.DataFrame:
    """
    Build the full feature + label dataset.

    Returns
    -------
    DataFrame with:
      - OHLCV columns
      - All requested factor columns (price / onchain / macro)
      - `log_ret_h`: LABEL — log(close[t+h] / close[t])
        NOTE: this is a FORWARD-looking quantity; it is only added
        at the very end and last `h` rows are dropped.
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
        provider = str(onchain_provider).strip().lower()
        if provider == "coinmetrics":
            raw_onchain = load_coinmetrics(
                metrics=onchain_metrics or [],
                asset=coinmetrics_asset,
                frequency=coinmetrics_frequency,
                start_time=coinmetrics_start_time,
                end_time=coinmetrics_end_time,
                cache_dir=coinmetrics_cache_dir,
                force=force_download,
            )
        else:
            raw_onchain = load_onchain(
                metrics=[
                    str(m) for m in (onchain_metrics or [])
                    if isinstance(m, str)
                ] or None,
                timespan=onchain_timespan,
                cache_dir=onchain_cache_dir,
                force=force_download,
            )
        onchain_df = clean_onchain(raw_onchain)
        if use_glassnode and glassnode_metrics:
            raw_gn = load_glassnode(
                metrics=glassnode_metrics,
                cache_dir=glassnode_cache_dir,
                force=force_download,
                api_key_env=glassnode_api_key_env,
                asset=glassnode_asset,
                interval=glassnode_interval,
            )
            gn_df = clean_onchain(raw_gn)
            onchain_df = pd.concat([onchain_df, gn_df], axis=1, join="outer")

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

    h = int(label_horizon_days) if label_horizon_days is not None else int(horizon)
    if h <= 0:
        raise ValueError("label_horizon_days must be a positive integer.")

    # ── 8. Build label (FORWARD shift — label at t uses close[t+h])
    # CRITICAL: shift(-h) must happen AFTER all feature calculations.
    # The label is unavailable at time t; it is only assigned here for
    # supervised learning purposes and must NEVER be a feature.
    data[LABEL_COL] = np.log(
        data["close"].shift(-h) / data["close"]
    )
    data[DIRECTION_LABEL_COL] = (data[LABEL_COL] > 0).astype(int)
    if drop_label_na:
        data = data.dropna(subset=[LABEL_COL]).copy()

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
        label_col, LABEL_COL, DIRECTION_LABEL_COL, "open", "high", "low", "close", "volume",
        "adj_close", "adj close",
    }
    return [c for c in df.columns if c not in non_feature]


def get_feature_cols_by_variant(
    df: pd.DataFrame,
    label_col: str = LABEL_COL,
    dataset_variant: str = "all",
) -> list[str]:
    """
    Return feature columns for one of the 7 dataset variants:
      onchain, ta, all, boruta_onchain, boruta_ta, boruta_all, univariate
    """
    variant = dataset_variant.lower().strip()
    base_cols = get_feature_cols(df, label_col=label_col)

    onchain_metric_names = {
        "n-transactions",
        "n-unique-addresses",
        "transaction-fees",
        "estimated-transaction-volume",
        "transfer-count",
        "mempool-size",
        "miners-revenue",
        "cost-per-transaction",
        "hash-rate",
        "difficulty",
        "block-count",
        "circulating-supply",
        "issuance",
        "market-cap-usd",
    }
    onchain_prefixes = (
        "ntx_",
        "addr_",
        "fees_",
        "txvol_",
        "txcnt_",
        "mempool_",
        "mrev_",
        "cptx_",
        "hr_",
        "diff_",
        "blk_",
        "supply_",
        "issuance_",
        "mcap_",
        "tx_per_addr",
        "mrev_per_hash",
    )
    ta_prefixes = (
        "mom_",
        "vol_",
        "ma",
        "amplitude",
        "hl_range_",
        "rsi_",
        "macd_",
        "williams_",
        "close_open_ret",
    )

    def _is_onchain(col: str) -> bool:
        if col in onchain_metric_names:
            return True
        return col.startswith(onchain_prefixes)

    def _is_ta(col: str) -> bool:
        # Treat classic price/technical factors as TA block.
        return col.startswith(ta_prefixes)

    if variant in ("all", "boruta_all"):
        return base_cols
    if variant in ("onchain", "boruta_onchain"):
        return [c for c in base_cols if _is_onchain(c)]
    if variant in ("ta", "boruta_ta"):
        return [c for c in base_cols if _is_ta(c)]
    if variant == "univariate":
        return ["close"] if "close" in df.columns else []

    raise ValueError(f"Unknown dataset_variant: {dataset_variant}")
