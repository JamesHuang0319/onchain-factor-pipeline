"""
src/features/macro_factors.py
──────────────────────────────────────────────────────────────
Macro factor module — STUB for Iter-0 / Iter-1.

In Iter-2 this module will pull real FRED data (DGS10, DTWEXBGS,
UNRATE, CPIAUCSL, FEDFUNDS) and apply release_lag_days to prevent
lookahead. For now it returns a dummy DataFrame of zeros so the
rest of the pipeline can run unmodified.

ANTI-LEAKAGE NOTE for Iter-2:
  - Always shift macro series by release_lag_days before joining.
  - Use ffill() (never bfill()) after reindexing to price calendar.
"""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def load_macro(
    index: pd.DatetimeIndex,
    release_lag_days: int = 1,
    use_dummy: bool = True,
    cache_dir: str = "data/raw/macro",
) -> pd.DataFrame:
    """
    Return a macro factor DataFrame aligned to `index`.

    Parameters
    ----------
    index            : target daily UTC DatetimeIndex (from price data)
    release_lag_days : days to shift raw macro series forward before
                       aligning (simulates publication delay)
    use_dummy        : if True, return zeros (Iter-0 / Iter-1 stub)
    cache_dir        : where real FRED CSVs would be cached (Iter-2)

    Returns
    -------
    DataFrame with macro factor columns, indexed by `index`.
    All values are 0.0 in stub mode.
    """
    if use_dummy:
        logger.info("[macro] Using dummy macro factors (stub mode).")
        dummy_cols = ["macro_dgs10", "macro_dxy", "macro_fedfunds"]
        return pd.DataFrame(0.0, index=index, columns=dummy_cols)

    # ── Iter-2 placeholder: load from FRED CSVs ────────────
    # TODO: implement FRED pull with fredapi or manual CSV
    # Example (Iter-2):
    #   from fredapi import Fred
    #   fred = Fred(api_key=os.environ["FRED_API_KEY"])
    #   dgs10 = fred.get_series("DGS10", start_date=..., end_date=...)
    #   dgs10 = dgs10.shift(release_lag_days)   # ← CRITICAL leakage guard
    #   ... merge and ffill onto index ...
    raise NotImplementedError(
        "Real macro data not yet implemented. Set use_dummy=True for Iter-0/1."
    )
