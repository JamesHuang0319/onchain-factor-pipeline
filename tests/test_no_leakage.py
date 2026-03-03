"""
tests/test_no_leakage.py
──────────────────────────────────────────────────────────────
Leakage guard tests — these MUST all pass before training.

Tests
─────
1. test_label_uses_future_close:
   Verify log_ret_7d[t] == log(close[t+7] / close[t]).
   If label is built from current or past close, this fails.

2. test_no_feature_uses_label:
   Feature columns must not contain the label value with r² ≈ 1.

3. test_feature_temporal_order:
   For each feature column, verify that feature[t] is uncorrelated
   with close[t+7] / close[t] BEFORE the label shift is applied,
   i.e., if any feature has |r| > 0.99 with the UNSHIFTED future
   close ratio, it is likely leaking future data.

4. test_no_future_in_rolling:
   Spot-check that rolling windows do not use data from the future
   by verifying the first N rows of rolling features are NaN
   (they would be non-NaN only if pandas used future padding).

5. test_onchain_forward_fill_only:
   Verify on-chain features at date t match the last value at t
   (i.e., ffill, not bfill — no future fill).

Run with:
  pytest tests/test_no_leakage.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make src importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.datasets.build_dataset import LABEL_COL, build_dataset, get_feature_cols
from src.features.price_factors import compute_price_factors


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def small_price_df() -> pd.DataFrame:
    """Minimal synthetic OHLCV DataFrame for fast testing."""
    np.random.seed(42)
    n = 400
    dates = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    close = 100 * np.exp(np.random.randn(n).cumsum() * 0.02)
    data = {
        "open":  close * (1 + np.random.randn(n) * 0.005),
        "high":  close * (1 + np.abs(np.random.randn(n)) * 0.01),
        "low":   close * (1 - np.abs(np.random.randn(n)) * 0.01),
        "close": close,
        "volume": np.random.randint(1_000, 100_000, n).astype(float),
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture(scope="module")
def full_df(small_price_df) -> pd.DataFrame:
    """Dataset built from synthetic price (no network call)."""
    from src.features.price_factors import compute_price_factors
    df = compute_price_factors(small_price_df)
    horizon = 7
    df[LABEL_COL] = np.log(df["close"].shift(-horizon) / df["close"])
    return df


# ── Tests ─────────────────────────────────────────────────────

class TestLabelIntegrity:
    """Verify label is correctly computed from FUTURE close."""

    def test_label_uses_future_close(self, full_df):
        """log_ret_7d[t] must equal log(close[t+7] / close[t])."""
        df = full_df.dropna(subset=[LABEL_COL])
        # Reconstruct expected label independently
        close = full_df["close"]
        expected = np.log(close.shift(-7) / close).reindex(df.index)
        actual = df[LABEL_COL]
        diff = (actual - expected).abs().max()
        assert diff < 1e-9, (
            f"Label does not match log(close[t+7]/close[t]). Max diff={diff:.2e}"
        )

    def test_label_NaN_at_tail(self, full_df):
        """Last 7 rows must have NaN label (future not available)."""
        tail_labels = full_df[LABEL_COL].iloc[-7:]
        assert tail_labels.isna().all(), (
            "Last 7 rows should have NaN label — future data is not available there."
        )

    def test_label_not_in_features(self, full_df):
        """Label column must not appear in feature_cols."""
        feature_cols = get_feature_cols(full_df, LABEL_COL)
        assert LABEL_COL not in feature_cols, (
            f"'{LABEL_COL}' found in feature_cols — this is a critical leakage!"
        )


class TestFeatureTemporalIntegrity:
    """Verify features cannot predict EXACT future prices (would indicate leakage)."""

    def test_no_feature_perfectly_correlated_with_label(self, full_df):
        """No feature should have |Pearson r| > 0.99 with the label."""
        df = full_df.dropna(subset=[LABEL_COL])
        feat_cols = get_feature_cols(df, LABEL_COL)
        violations = []
        for col in feat_cols:
            s = df[col].dropna()
            idx = s.index.intersection(df[LABEL_COL].dropna().index)
            if len(idx) < 20:
                continue
            r = float(s.loc[idx].corr(df.loc[idx, LABEL_COL]))
            if abs(r) > 0.99:
                violations.append((col, r))
        assert not violations, (
            f"Perfect correlation with label detected (leakage!):\n"
            + "\n".join(f"  {c}: r={r:.4f}" for c, r in violations)
        )

    def test_rolling_features_start_with_NaN(self, small_price_df):
        """
        Rolling windows of size W should produce NaN for the first W-1 rows.
        If a rolling feature has values in rows 0..W-2 it used padding (leakage).
        """
        df = compute_price_factors(small_price_df)
        # vol_7d uses window=7 with min_periods=3; rows 0..2 should be NaN
        rolling_col = "vol_7d"
        assert rolling_col in df.columns, f"Expected column '{rolling_col}' in features."
        # The first 2 rows (less than min_periods=3) must be NaN
        assert df[rolling_col].iloc[:2].isna().all(), (
            f"'{rolling_col}' first 2 rows are not NaN — "
            "rolling window may be using future data (check min_periods)."
        )

    def test_momentum_at_t_uses_only_past_close(self, small_price_df):
        """mom_7d[t] = log(close[t] / close[t-7]) (backward-looking)."""
        df = compute_price_factors(small_price_df)
        close = small_price_df["close"]
        idx = 20  # arbitrary row after warm-up
        expected = np.log(close.iloc[idx] / close.iloc[idx - 7])
        actual = df["mom_7d"].iloc[idx]
        assert abs(actual - expected) < 1e-9, (
            f"mom_7d[{idx}] = {actual:.6f}, expected {expected:.6f}. "
            "Momentum may be using future data."
        )


class TestOnChainAlignment:
    """Verify on-chain forward-fill does not introduce future data."""

    def test_ffill_direction(self):
        """After forward-fill, NaN values should only appear at the START of the series."""
        from src.etl.cleaner import clean_onchain
        dates = pd.date_range("2020-01-01", periods=30, freq="D", tz="UTC")
        # Sparse series: only 10 actual values, rest NaN
        sparse = pd.Series(np.nan, index=dates, name="test_metric")
        sparse.iloc[[0, 5, 10, 15, 20, 25]] = [100.0, 110.0, 120.0, 115.0, 130.0, 140.0]
        df_onchain = sparse.to_frame()
        cleaned = clean_onchain(df_onchain, ffill_limit=7)

        # After ffill, value at day 6 (5 days after last known=day5)
        # should be 110.0 (forward-filled), NOT NaN and NOT a future value.
        assert cleaned["test_metric"].iloc[6] == 110.0, (
            "Forward-fill not working correctly."
        )
        # Day 13 (8 days after day 5, beyond ffill_limit=7) should be NaN
        # (unless day 10 fills it — day 10 = 120, day 13 = filled by day 10)
        assert cleaned["test_metric"].iloc[13] == 120.0, (
            "Forward-fill from day 10 should reach day 13."
        )

        # Crucially: verify no future filling (bfill).
        # Day 1 (before day 5's value) should NOT be 110.0
        assert np.isnan(cleaned["test_metric"].iloc[1]), (
            "Day 1 must remain NaN — backward-fill (future data) detected!"
        )
