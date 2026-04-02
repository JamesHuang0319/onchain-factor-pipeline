"""
src/ingest/coinmetrics.py
──────────────────────────────────────────────────────────────
Download on-chain metrics from Coin Metrics Community API with:
  - file-based caching (CSV under data/raw/coinmetrics/)
  - retry with exponential backoff
  - UTC daily alignment

Community API endpoint:
  https://community-api.coinmetrics.io/v4/timeseries/asset-metrics
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
RETRY_DELAYS = [1, 2, 4]


def _normalize_name(name: str) -> str:
    out = name.strip().lower()
    for ch in [" ", "-", "/", "(", ")", ".", ",", ":", ";", "[", "]"]:
        out = out.replace(ch, "_")
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


def _metric_cache_path(metric_name: str, cache_dir: str | Path) -> Path:
    return Path(cache_dir) / f"{_normalize_name(metric_name)}.csv"


def _parse_metric_entry(metric: dict[str, Any] | str) -> tuple[str, str]:
    if isinstance(metric, str):
        name = metric
        code = metric
    else:
        name = str(metric.get("name") or metric.get("metric") or "").strip()
        code = str(metric.get("metric") or metric.get("name") or "").strip()
    if not name or not code:
        raise ValueError(f"Invalid Coin Metrics metric entry: {metric}")
    return name, code


def download_coinmetrics_metric(
    metric: dict[str, Any] | str,
    asset: str = "btc",
    frequency: str = "1d",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    cache_dir: str | Path = "data/raw/coinmetrics",
    force: bool = False,
) -> pd.DataFrame:
    """
    Download one Coin Metrics asset metric as a daily UTC series.
    """
    metric_name, metric_code = _parse_metric_entry(metric)
    cache_path = _metric_cache_path(metric_name, cache_dir)
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    if cache_path.exists() and not force:
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True).normalize()
        df = df[~df.index.duplicated(keep="last")].sort_index()
        return df

    params = {
        "assets": asset,
        "metrics": metric_code,
        "frequency": frequency,
        "page_size": 10000,
    }
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time

    rows: list[dict[str, Any]] = []
    next_url: Optional[str] = BASE_URL
    last_exc: Exception | None = None

    while next_url:
        for attempt, delay in enumerate(RETRY_DELAYS, start=1):
            try:
                resp = requests.get(next_url, params=params, timeout=45)
                resp.raise_for_status()
                payload = resp.json()
                break
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    f"[coinmetrics] Attempt {attempt} failed for {metric_name}: {exc}. "
                    f"Retrying in {delay}s …"
                )
                time.sleep(delay)
        else:
            raise RuntimeError(
                f"[coinmetrics] All retries exhausted for metric {metric_name} ({metric_code})."
            ) from last_exc

        batch = payload.get("data", [])
        rows.extend(batch)
        next_url = payload.get("next_page_url")
        params = None

    if not rows:
        raise ValueError(f"[coinmetrics] Empty response for metric {metric_name} ({metric_code})")

    records: list[dict[str, Any]] = []
    for item in rows:
        ts = item.get("time")
        value = item.get(metric_code)
        if ts is None:
            continue
        records.append(
            {
                "date": pd.to_datetime(ts, utc=True).normalize(),
                metric_name: pd.to_numeric(value, errors="coerce"),
            }
        )

    if not records:
        raise ValueError(f"[coinmetrics] No valid points parsed for {metric_name} ({metric_code})")

    df = pd.DataFrame(records).set_index("date").sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df.to_csv(cache_path)
    logger.info(f"[coinmetrics] Saved {len(df)} rows → {cache_path}")
    return df


def load_coinmetrics(
    metrics: list[dict[str, Any] | str],
    asset: str = "btc",
    frequency: str = "1d",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    cache_dir: str | Path = "data/raw/coinmetrics",
    force: bool = False,
) -> pd.DataFrame:
    """
    Download/merge configured Coin Metrics asset metrics.
    """
    frames: list[pd.DataFrame] = []
    for metric in metrics:
        try:
            frames.append(
                download_coinmetrics_metric(
                    metric=metric,
                    asset=asset,
                    frequency=frequency,
                    start_time=start_time,
                    end_time=end_time,
                    cache_dir=cache_dir,
                    force=force,
                )
            )
        except Exception as exc:
            logger.error(f"[coinmetrics] Skipping metric {metric}: {exc}")

    if not frames:
        raise RuntimeError("[coinmetrics] No metrics downloaded successfully.")

    return pd.concat(frames, axis=1, join="outer").sort_index()
