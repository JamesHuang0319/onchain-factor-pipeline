"""
src/evaluation/walk_forward.py
──────────────────────────────────────────────────────────────
Walk-forward cross-validation for time-series models.

ANTI-LEAKAGE DESIGN:
  - Train set: all data strictly BEFORE the val/test window start.
  - Val set   : used only for early-stopping / hyperparameter selection.
  - Test set  : predictions made at t use only training data from [0, t).
  - No shuffling. Chronological order is sacred.

Default (from data.yaml):
  train=3y, val=6m, test=6m, step=3m  (expanding or rolling window)
Fallback: 70/30 chronological split when total rows < min_rows.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterator, Optional

import numpy as np
import pandas as pd

from src.evaluation.metrics import ic, mae, mse, oos_r2, rank_ic

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardFold:
    fold_id: int
    train_idx: pd.DatetimeIndex
    val_idx: pd.DatetimeIndex
    test_idx: pd.DatetimeIndex


@dataclass
class FoldResult:
    fold_id: int
    test_dates: pd.DatetimeIndex
    y_true: np.ndarray
    y_pred: np.ndarray
    metrics: dict[str, float] = field(default_factory=dict)


def generate_folds(
    index: pd.DatetimeIndex,
    train_years: float = 3.0,
    val_months: float = 6.0,
    test_months: float = 6.0,
    step_months: float = 3.0,
    wf_type: str = "expanding",  # "expanding" | "rolling"
    min_rows: int = 500,
) -> list[WalkForwardFold]:
    """
    Generate walk-forward fold indices.

    Parameters
    ----------
    index       : full UTC DatetimeIndex of the dataset
    train_years : initial training window size
    val_months  : validation window size
    test_months : out-of-sample test window size
    step_months : how far forward each fold moves
    wf_type     : "expanding" keeps growing train set;
                  "rolling" uses a fixed-size train window
    min_rows    : if total rows < this, use 70/30 fallback

    Returns
    -------
    List of WalkForwardFold objects (chronological order).
    """
    n = len(index)

    # ── Fallback: 70/30 chronological split ───────────────────
    if n < min_rows:
        logger.warning(
            f"[walk_forward] Only {n} rows (< {min_rows}). "
            "Using 70/30 chronological split."
        )
        split = int(n * 0.7)
        val_split = int(n * 0.85)
        return [
            WalkForwardFold(
                fold_id=0,
                train_idx=index[:split],
                val_idx=index[split:val_split],
                test_idx=index[val_split:],
            )
        ]

    # ── Build date offsets ────────────────────────────────────
    train_delta = pd.DateOffset(years=int(train_years),
                                months=int((train_years % 1) * 12))
    val_delta   = pd.DateOffset(months=int(val_months))
    test_delta  = pd.DateOffset(months=int(test_months))
    step_delta  = pd.DateOffset(months=int(step_months))

    folds: list[WalkForwardFold] = []
    fold_id = 0
    # First train window ends at index[0] + train_delta
    train_start = index[0]
    train_end   = train_start + train_delta

    while True:
        val_start  = train_end
        val_end    = val_start + val_delta
        test_start = val_end
        test_end   = test_start + test_delta

        if test_end > index[-1] + pd.DateOffset(days=1):
            break

        train_mask = (index >= train_start) & (index < val_start)
        val_mask   = (index >= val_start)   & (index < test_start)
        test_mask  = (index >= test_start)  & (index < test_end)

        if train_mask.sum() == 0 or test_mask.sum() == 0:
            break

        folds.append(
            WalkForwardFold(
                fold_id=fold_id,
                train_idx=index[train_mask],
                val_idx=index[val_mask],
                test_idx=index[test_mask],
            )
        )
        fold_id += 1

        # Advance
        if wf_type == "rolling":
            train_start = train_start + step_delta
        train_end = train_end + step_delta

    if not folds:
        raise RuntimeError(
            "[walk_forward] No valid folds generated. "
            "Check that your dataset spans enough time."
        )

    logger.info(f"[walk_forward] Generated {len(folds)} folds ({wf_type}).")
    return folds


def run_walk_forward(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    model_cls,
    model_config: dict,
    train_years: float = 3.0,
    val_months: float = 6.0,
    test_months: float = 6.0,
    step_months: float = 3.0,
    wf_type: str = "expanding",
    min_rows: int = 500,
) -> tuple[list[FoldResult], pd.DataFrame]:
    """
    Execute walk-forward cross-validation.

    Parameters
    ----------
    df           : full dataset (features + label, no NaN in label)
    feature_cols : list of feature column names
    label_col    : target column name
    model_cls    : BaseModel subclass (not instance)
    model_config : dict of model hyperparameters
    ...          : walk-forward split params (see generate_folds)

    Returns
    -------
    (fold_results, predictions_df)
      fold_results   : list of FoldResult with per-fold metrics
      predictions_df : DataFrame with columns [y_true, y_pred] for all
                       out-of-sample test periods (concatenated)
    """
    # Drop NaN labels — CRITICAL (last horizon rows have NaN label)
    df_clean = df.dropna(subset=[label_col]).copy()

    folds = generate_folds(
        index=df_clean.index,
        train_years=train_years,
        val_months=val_months,
        test_months=test_months,
        step_months=step_months,
        wf_type=wf_type,
        min_rows=min_rows,
    )

    all_results: list[FoldResult] = []
    pred_frames: list[pd.DataFrame] = []

    for fold in folds:
        # ── Slice data by date index ──────────────────────────
        train_df = df_clean.loc[df_clean.index.isin(fold.train_idx)]
        val_df   = df_clean.loc[df_clean.index.isin(fold.val_idx)]
        test_df  = df_clean.loc[df_clean.index.isin(fold.test_idx)]

        if len(train_df) == 0 or len(test_df) == 0:
            logger.warning(f"[walk_forward] Fold {fold.fold_id}: empty slice, skip.")
            continue

        # ── Drop rows with NaN features (rolling warm-up rows) ──
        # Rolling indicators (vol_30d, ma60_dev, …) are NaN for the
        # first 60+ rows; sklearn models cannot handle NaN inputs.
        all_cols = feature_cols + [label_col]
        train_df = train_df.dropna(subset=feature_cols)
        val_df   = val_df.dropna(subset=feature_cols)
        test_df  = test_df.dropna(subset=feature_cols)

        if len(train_df) == 0 or len(test_df) == 0:
            logger.warning(
                f"[walk_forward] Fold {fold.fold_id}: all NaN after feature dropna, skip."
            )
            continue

        X_train = train_df[feature_cols]
        y_train = train_df[label_col].values
        X_val   = val_df[feature_cols]   if len(val_df) else None
        y_val   = val_df[label_col].values   if len(val_df) else None
        X_test  = test_df[feature_cols]
        y_test  = test_df[label_col].values

        # ── Train fresh model per fold ────────────────────────
        model = model_cls(config=model_config)
        model.fit(X_train, y_train, X_val, y_val)
        y_pred = model.predict(X_test)

        y_bench = np.full_like(y_test, fill_value=float(np.mean(y_train)), dtype=float)
        metrics = {
            "IC": ic(y_test, y_pred),
            "RankIC": rank_ic(y_test, y_pred),
            "OOS_R2": oos_r2(y_test, y_pred, y_bench),
            "MAE": mae(y_test, y_pred),
            "MSE": mse(y_test, y_pred),
            "n_samples": float(len(y_test)),
            "start_date": test_df.index.min(),
            "end_date": test_df.index.max(),
        }

        result = FoldResult(
            fold_id=fold.fold_id,
            test_dates=test_df.index,
            y_true=y_test,
            y_pred=y_pred,
            metrics=metrics,
        )
        all_results.append(result)

        pred_frames.append(
            pd.DataFrame(
                {"y_true": y_test, "y_pred": y_pred},
                index=test_df.index,
            )
        )

        logger.info(
            f"[walk_forward] Fold {fold.fold_id}: "
            f"train={len(train_df)}, test={len(test_df)}, "
            f"MAE={metrics['MAE']:.4f}, "
            f"RankIC={metrics['RankIC']:.4f}"
        )

    if not pred_frames:
        raise RuntimeError("[walk_forward] No fold produced predictions.")

    predictions_df = pd.concat(pred_frames).sort_index()
    return all_results, predictions_df


def fold_results_to_table(
    fold_results: list[FoldResult],
    config_name: str,
    model_name: str,
) -> pd.DataFrame:
    """Convert fold outputs into the required IC table schema."""
    rows: list[dict] = []
    for fr in fold_results:
        m = fr.metrics
        rows.append(
            {
                "config_name": config_name,
                "model_name": model_name,
                "fold_id": fr.fold_id,
                "start_date": pd.Timestamp(m["start_date"]).date().isoformat(),
                "end_date": pd.Timestamp(m["end_date"]).date().isoformat(),
                "IC": float(m["IC"]),
                "RankIC": float(m["RankIC"]),
                "OOS_R2": float(m["OOS_R2"]),
                "MAE": float(m["MAE"]),
                "MSE": float(m["MSE"]),
                "n_samples": int(m["n_samples"]),
            }
        )
    return pd.DataFrame(rows)
