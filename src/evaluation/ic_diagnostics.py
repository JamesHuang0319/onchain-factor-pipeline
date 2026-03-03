"""
Utilities for Iter-1D IC diagnostics export and visualization.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def upsert_rows(path: Path, new_df: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    """Upsert rows by key columns and persist to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        prev = pd.read_csv(path)
        if not prev.empty:
            keys = set(tuple(x) for x in new_df[key_cols].astype(str).to_numpy())
            prev = prev[~prev[key_cols].astype(str).apply(tuple, axis=1).isin(keys)]
            new_df = pd.concat([prev, new_df], ignore_index=True)
    new_df.to_csv(path, index=False, encoding="utf-8")
    return new_df


def summarize_ic(fold_df: pd.DataFrame) -> dict[str, float]:
    """Compute fold-level IC diagnostics summary."""
    ic_series = pd.to_numeric(fold_df["IC"], errors="coerce").dropna()
    if ic_series.empty:
        return {
            "IC_mean": float("nan"),
            "IC_median": float("nan"),
            "IC_std": float("nan"),
            "IC_negative_ratio": float("nan"),
            "best_fold_ic": float("nan"),
            "worst_fold_ic": float("nan"),
        }
    return {
        "IC_mean": float(ic_series.mean()),
        "IC_median": float(ic_series.median()),
        "IC_std": float(ic_series.std(ddof=1)),
        "IC_negative_ratio": float((ic_series < 0).mean()),
        "best_fold_ic": float(ic_series.max()),
        "worst_fold_ic": float(ic_series.min()),
    }


def sample_alignment_rows(pred_df: pd.DataFrame, n: int = 3, seed: int = 42) -> pd.DataFrame:
    """Randomly sample n rows for alignment sanity diagnostics."""
    cols = ["y_pred", "y_true", "close_t", "close_t_plus_h", "manual_log_return", "alignment_abs_err"]
    available = pred_df.dropna(subset=cols)
    if available.empty:
        return available
    n = min(n, len(available))
    return available.sample(n=n, random_state=seed).sort_index()


def generate_ic_figures(diag_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Generate static Matplotlib PDFs for IC diagnostics."""
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    configs = {
        "iter0_price_only": out_dir / "ic_hist_price_only.pdf",
        "iter1_price_onchain": out_dir / "ic_hist_price_onchain.pdf",
    }
    for config_name, out_path in configs.items():
        subset = diag_df[diag_df["config_name"] == config_name]
        if subset.empty:
            continue
        plt.figure(figsize=(6, 4))
        plt.hist(subset["IC"].astype(float), bins=10, edgecolor="black")
        plt.title(f"IC Histogram: {config_name}")
        plt.xlabel("IC")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(out_path, format="pdf")
        plt.close()
        generated.append(out_path)

    # Box compare: IC by config
    compare = diag_df[diag_df["config_name"].isin(["iter0_price_only", "iter1_price_onchain"])]
    if not compare.empty:
        plt.figure(figsize=(6, 4))
        groups = [
            compare[compare["config_name"] == "iter0_price_only"]["IC"].astype(float).dropna(),
            compare[compare["config_name"] == "iter1_price_onchain"]["IC"].astype(float).dropna(),
        ]
        labels = ["price_only", "price_onchain"]
        plt.boxplot(groups, labels=labels, showmeans=True)
        plt.title("Fold IC Comparison")
        plt.ylabel("IC")
        plt.tight_layout()
        out_path = out_dir / "ic_box_compare.pdf"
        plt.savefig(out_path, format="pdf")
        plt.close()
        generated.append(out_path)

        # OOS_R2 bar compare (mean by config)
        agg = compare.groupby("config_name", as_index=False)["OOS_R2"].mean()
        plt.figure(figsize=(6, 4))
        plt.bar(agg["config_name"], agg["OOS_R2"], edgecolor="black")
        plt.title("Mean Fold OOS R2 Comparison")
        plt.ylabel("OOS_R2")
        plt.tight_layout()
        out_path = out_dir / "oos_r2_bar_compare.pdf"
        plt.savefig(out_path, format="pdf")
        plt.close()
        generated.append(out_path)

    return generated
