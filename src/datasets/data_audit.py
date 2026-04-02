from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class DataAuditResult:
    summary: pd.DataFrame
    missing_top: pd.DataFrame
    split_info: pd.DataFrame
    class_balance: pd.DataFrame


def _safe_ratio(num: float, den: float) -> float:
    return float(num / den) if den else float("nan")


def run_data_audit(
    df: pd.DataFrame,
    label_col: str,
    classification_label_col: str,
    feature_cols: list[str],
    train_ratio: float = 0.8,
) -> DataAuditResult:
    n_rows = int(len(df))
    n_features = int(len(feature_cols))
    n_cols = int(df.shape[1])
    idx_min = pd.Timestamp(df.index.min()) if n_rows else pd.NaT
    idx_max = pd.Timestamp(df.index.max()) if n_rows else pd.NaT

    label_na = int(df[label_col].isna().sum()) if label_col in df.columns else n_rows
    label_missing_ratio = _safe_ratio(label_na, n_rows)

    feature_missing = (
        df[feature_cols].isna().mean().sort_values(ascending=False)
        if feature_cols
        else pd.Series(dtype=float)
    )
    missing_top = (
        feature_missing.head(20).rename("missing_ratio").to_frame()
        if not feature_missing.empty
        else pd.DataFrame(columns=["missing_ratio"])
    )

    cut = max(1, int(n_rows * train_ratio))
    train_rows = int(cut)
    test_rows = int(max(0, n_rows - cut))
    split_info = pd.DataFrame(
        [
            {
                "train_ratio": float(train_ratio),
                "train_rows": train_rows,
                "test_rows": test_rows,
                "train_start": idx_min.date().isoformat() if pd.notna(idx_min) else None,
                "train_end": (
                    pd.Timestamp(df.index[min(cut - 1, max(0, n_rows - 1))]).date().isoformat()
                    if n_rows
                    else None
                ),
                "test_start": (
                    pd.Timestamp(df.index[cut]).date().isoformat() if cut < n_rows else None
                ),
                "test_end": idx_max.date().isoformat() if pd.notna(idx_max) else None,
            }
        ]
    )

    if classification_label_col in df.columns and n_rows:
        cls = df[classification_label_col].dropna().astype(int)
        pos = int((cls == 1).sum())
        neg = int((cls == 0).sum())
        class_balance = pd.DataFrame(
            [
                {
                    "n_total": int(len(cls)),
                    "n_positive": pos,
                    "n_negative": neg,
                    "positive_ratio": _safe_ratio(pos, len(cls)),
                    "negative_ratio": _safe_ratio(neg, len(cls)),
                }
            ]
        )
    else:
        class_balance = pd.DataFrame(
            [
                {
                    "n_total": 0,
                    "n_positive": 0,
                    "n_negative": 0,
                    "positive_ratio": float("nan"),
                    "negative_ratio": float("nan"),
                }
            ]
        )

    summary = pd.DataFrame(
        [
            {
                "rows": n_rows,
                "columns": n_cols,
                "feature_count": n_features,
                "start_date": idx_min.date().isoformat() if pd.notna(idx_min) else None,
                "end_date": idx_max.date().isoformat() if pd.notna(idx_max) else None,
                "label_missing_ratio": label_missing_ratio,
                "feature_missing_ratio_mean": float(feature_missing.mean())
                if not feature_missing.empty
                else float("nan"),
                "feature_missing_ratio_max": float(feature_missing.max())
                if not feature_missing.empty
                else float("nan"),
            }
        ]
    )
    return DataAuditResult(
        summary=summary,
        missing_top=missing_top,
        split_info=split_info,
        class_balance=class_balance,
    )


def save_data_audit(result: DataAuditResult, out_dir: str | Path) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": out / "summary.csv",
        "missing_top": out / "missing_top20.csv",
        "split_info": out / "split_info.csv",
        "class_balance": out / "class_balance.csv",
    }
    result.summary.to_csv(paths["summary"], index=False, encoding="utf-8")
    result.missing_top.to_csv(paths["missing_top"], index=True, encoding="utf-8")
    result.split_info.to_csv(paths["split_info"], index=False, encoding="utf-8")
    result.class_balance.to_csv(paths["class_balance"], index=False, encoding="utf-8")
    return paths

