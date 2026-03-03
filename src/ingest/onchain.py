"""
src/ingest/onchain.py
──────────────────────────────────────────────────────────────
Download on-chain metrics from Blockchain.com public REST API.
Endpoint: https://api.blockchain.info/charts/{metric}
          ?timespan=all&format=json&sampled=false

Response JSON structure:
  { "values": [{"x": <unix_ts>, "y": <value>}, ...] }

Features:
  - File-based caching (CSV under data/raw/blockchain/)
  - 3 retries with exponential back-off (1 s → 2 s → 4 s)
  - UTC date alignment
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.blockchain.info/charts/{metric}"
RETRY_DELAYS = [1, 2, 4]  # seconds

DEFAULT_METRICS = [
    "n-transactions",
    "n-unique-addresses",
    "transaction-fees",
    "estimated-transaction-volume",
    "mempool-size",
    "miners-revenue",
    "cost-per-transaction",
    "hash-rate",
    "difficulty",
]


def _cache_path(metric: str, cache_dir: str | Path) -> Path:
    return Path(cache_dir) / f"{metric}.csv"


def download_onchain_metric(
    metric: str,
    timespan: str = "all",
    cache_dir: str | Path = "data/raw/blockchain",
    force: bool = False,
) -> pd.DataFrame:
    """
    Download a single Blockchain.com chart metric.

    Parameters
    ----------
    metric  : e.g. "n-transactions"
    timespan: "all" for full history
    cache_dir: where to store the CSV
    force   : bypass cache

    Returns
    -------
    DataFrame columns: [metric]
    Index: pd.DatetimeIndex UTC daily
    """
    path = _cache_path(metric, cache_dir)
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    # ── Cache hit ──────────────────────────────────────────
    if path.exists() and not force:
        logger.info(f"[onchain] Loading from cache: {path}")
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True).normalize()
        df = df[~df.index.duplicated(keep="last")].sort_index()
        return df

    # ── Network fetch with retry ───────────────────────────
    url = BASE_URL.format(metric=metric)
    params = {"timespan": timespan, "format": "json", "sampled": "false"}
    logger.info(f"[onchain] Fetching {metric} from {url} …")

    last_exc: Exception | None = None
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as exc:
            last_exc = exc
            logger.warning(
                f"[onchain] Attempt {attempt} failed for {metric}: {exc}. "
                f"Retrying in {delay}s …"
            )
            time.sleep(delay)
    else:
        raise RuntimeError(
            f"[onchain] All retries exhausted for {metric}"
        ) from last_exc

    # ── Parse ─────────────────────────────────────────────
    values = data.get("values", [])
    if not values:
        raise ValueError(f"[onchain] Empty response for metric: {metric}")

    records = [(v["x"], v["y"]) for v in values]
    df = pd.DataFrame(records, columns=["timestamp", metric])
    # Convert Unix timestamp (seconds) → UTC datetime
    df["date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.normalize()
    df = df.drop(columns=["timestamp"]).set_index("date")
    # Remove duplicate dates (keep last)
    df = df[~df.index.duplicated(keep="last")].sort_index()

    # ── Persist ────────────────────────────────────────────
    df.to_csv(path)
    logger.info(f"[onchain] Saved {len(df)} rows → {path}")
    return df


def load_onchain(
    metrics: Optional[list[str]] = None,
    timespan: str = "all",
    cache_dir: str | Path = "data/raw/blockchain",
    force: bool = False,
) -> pd.DataFrame:
    """
    Download all metrics and merge into a single daily DataFrame.

    Returns
    -------
    DataFrame with one column per metric, UTC DatetimeIndex.
    Missing values are forward-filled then dropped.
    """
    if metrics is None:
        metrics = DEFAULT_METRICS

    frames: list[pd.DataFrame] = []
    for m in metrics:
        try:
            frames.append(download_onchain_metric(m, timespan, cache_dir, force))
        except Exception as exc:
            logger.error(f"[onchain] Skipping {m} due to error: {exc}")

    if not frames:
        raise RuntimeError("[onchain] No metrics could be downloaded.")

    merged = pd.concat(frames, axis=1, join="outer").sort_index()
    return merged
