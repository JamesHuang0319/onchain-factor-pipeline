"""
src/ingest/price.py
──────────────────────────────────────────────────────────────
Download OHLCV price data via yfinance with:
  - File-based caching (CSV under data/raw/yfinance/)
  - 3 retries with exponential back-off (1 s → 2 s → 4 s)
  - UTC date alignment (daily frequency)
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

RETRY_DELAYS = [1, 2, 4]  # seconds between retries


def _cache_path(symbol: str, cache_dir: str | Path) -> Path:
    """Return the CSV path for a given symbol."""
    return Path(cache_dir) / f"{symbol.replace('-', '_')}.csv"


def download_price(
    symbol: str,
    start_date: str = "2018-01-01",
    end_date: Optional[str] = None,
    cache_dir: str | Path = "data/raw/yfinance",
    force: bool = False,
) -> pd.DataFrame:
    """
    Download daily OHLCV for `symbol` from yfinance.

    Parameters
    ----------
    symbol     : e.g. "BTC-USD"
    start_date : ISO date string
    end_date   : ISO date string or None (→ today)
    cache_dir  : directory to store cached CSVs
    force      : if True, re-download even when cache exists

    Returns
    -------
    DataFrame with columns: open high low close volume adj_close
    Index: pd.DatetimeIndex (UTC, daily)

    Notes
    -----
    Anti-leakage: the close on date t is the closing price AT END
    of day t.  Any feature built from this series at time t must
    use only data[: t].  Labels are computed via shift(-horizon)
    in build_dataset.py.
    """
    path = _cache_path(symbol, cache_dir)
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    # ── Cache hit ────────────────────────────────────────────
    if path.exists() and not force:
        logger.info(f"[price] Loading from cache: {path}")
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True).normalize()
        return df

    # ── Network fetch with retry ─────────────────────────────
    logger.info(f"[price] Downloading {symbol} from yfinance …")
    last_exc: Exception | None = None
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            raw = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                auto_adjust=False,
                progress=False,
            )
            if raw.empty:
                raise ValueError(f"yfinance returned empty DataFrame for {symbol}")
            break
        except Exception as exc:
            last_exc = exc
            logger.warning(
                f"[price] Attempt {attempt} failed for {symbol}: {exc}. "
                f"Retrying in {delay}s …"
            )
            time.sleep(delay)
    else:
        raise RuntimeError(
            f"[price] All retries exhausted for {symbol}"
        ) from last_exc

    # ── Normalise columns ────────────────────────────────────
    # yfinance may return MultiIndex columns when downloading single ticker
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [col[0].lower() for col in raw.columns]
    else:
        raw.columns = [c.lower() for c in raw.columns]

    raw = raw.rename(columns={"adj close": "adj_close"})

    # ── UTC alignment ────────────────────────────────────────
    if raw.index.tz is None:
        raw.index = raw.index.tz_localize("UTC")
    else:
        raw.index = raw.index.tz_convert("UTC")
    raw.index = raw.index.normalize()
    raw.index.name = "date"

    # ── Persist ──────────────────────────────────────────────
    raw.to_csv(path)
    logger.info(f"[price] Saved {len(raw)} rows → {path}")
    return raw


def load_prices(
    symbols: list[str],
    start_date: str = "2018-01-01",
    end_date: Optional[str] = None,
    cache_dir: str | Path = "data/raw/yfinance",
    force: bool = False,
) -> dict[str, pd.DataFrame]:
    """Download and return a dict {symbol: OHLCV DataFrame}."""
    return {
        sym: download_price(sym, start_date, end_date, cache_dir, force)
        for sym in symbols
    }
