"""
src/ingest/glassnode.py
──────────────────────────────────────────────────────────────
Download on-chain metrics from Glassnode API with:
  - file-based caching (CSV under data/raw/glassnode/)
  - retry with exponential backoff
  - UTC daily alignment

Expected endpoint:
  https://api.glassnode.com/v1/metrics/{path}
Query params:
  a=<asset>, i=<interval>, api_key=<key>
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.glassnode.com/v1/metrics/{path}"
RETRY_DELAYS = [1, 2, 4]


def _normalize_name(name: str) -> str:
    out = name.strip().lower()
    out = out.replace("%", "pct")
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
        path = metric
    else:
        name = str(metric.get("name") or metric.get("path") or "").strip()
        path = str(metric.get("path") or "").strip()
    if not name or not path:
        raise ValueError(f"Invalid Glassnode metric entry: {metric}")
    return name, path


def download_glassnode_metric(
    metric: dict[str, Any] | str,
    api_key: str,
    asset: str = "BTC",
    interval: str = "24h",
    cache_dir: str | Path = "data/raw/glassnode",
    force: bool = False,
) -> pd.DataFrame:
    """
    Download one Glassnode metric as daily UTC series.
    Returns DataFrame indexed by date with one or more columns.
    """
    metric_name, metric_path = _parse_metric_entry(metric)
    cache_path = _metric_cache_path(metric_name, cache_dir)
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    if cache_path.exists() and not force:
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True).normalize()
        df = df[~df.index.duplicated(keep="last")].sort_index()
        return df

    url = BASE_URL.format(path=metric_path)
    params = {"a": asset, "i": interval, "api_key": api_key}
    last_exc: Exception | None = None
    data: Any = None

    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            resp = requests.get(url, params=params, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as exc:
            last_exc = exc
            logger.warning(
                f"[glassnode] Attempt {attempt} failed for {metric_name}: {exc}. "
                f"Retrying in {delay}s …"
            )
            time.sleep(delay)
    else:
        raise RuntimeError(
            f"[glassnode] All retries exhausted for metric {metric_name} ({metric_path})."
        ) from last_exc

    if not isinstance(data, list) or not data:
        raise ValueError(f"[glassnode] Empty/invalid response for metric {metric_name}")

    rows: list[dict[str, Any]] = []
    for item in data:
        t = item.get("t")
        v = item.get("v")
        if t is None:
            continue
        ts = pd.to_datetime(int(t), unit="s", utc=True).normalize()
        rec: dict[str, Any] = {"date": ts}
        if isinstance(v, dict):
            for k, val in v.items():
                rec[f"{_normalize_name(metric_name)}__{_normalize_name(str(k))}"] = val
        else:
            rec[_normalize_name(metric_name)] = v
        rows.append(rec)

    if not rows:
        raise ValueError(f"[glassnode] No valid points parsed for metric {metric_name}")

    df = pd.DataFrame(rows).set_index("date").sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df.to_csv(cache_path)
    logger.info(f"[glassnode] Saved {len(df)} rows → {cache_path}")
    return df


def load_glassnode(
    metrics: list[dict[str, Any] | str],
    cache_dir: str | Path = "data/raw/glassnode",
    force: bool = False,
    api_key_env: str = "GLASSNODE_API_KEY",
    asset: str = "BTC",
    interval: str = "24h",
) -> pd.DataFrame:
    """
    Download/merge configured Glassnode metrics.
    """
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key:
        raise RuntimeError(
            f"[glassnode] Missing API key. Set env var {api_key_env}."
        )
    frames: list[pd.DataFrame] = []
    for metric in metrics:
        try:
            frames.append(
                download_glassnode_metric(
                    metric=metric,
                    api_key=api_key,
                    asset=asset,
                    interval=interval,
                    cache_dir=cache_dir,
                    force=force,
                )
            )
        except Exception as exc:
            logger.error(f"[glassnode] Skipping metric {metric}: {exc}")

    if not frames:
        raise RuntimeError("[glassnode] No metrics downloaded successfully.")

    merged = pd.concat(frames, axis=1, join="outer").sort_index()
    return merged

