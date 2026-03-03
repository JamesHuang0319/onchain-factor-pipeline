"""
src/visualization/matplotlib_reports.py
──────────────────────────────────────────────────────────────
Static publication-quality figures (PDF) for the thesis report.

Exports:
  - Equity curves (per model, per cost)
  - Prediction vs. actual scatter / time-series
  - Drawdown plot
  - Metric comparison bar chart (cross-experiment)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")          # non-interactive backend for file export
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

FIGURE_DIR = Path("reports/figures")
DPI = 150
STYLE = "seaborn-v0_8-whitegrid"


def _save(fig: plt.Figure, name: str, out_dir: Path = FIGURE_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_equity_curves(
    equity_dict: dict[str, pd.Series],
    title: str = "Equity Curves",
    out_dir: Path = FIGURE_DIR,
    filename: str = "equity_curves.pdf",
) -> Path:
    """Plot multiple equity curves on one axis."""
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(12, 5))
        for label, equity in equity_dict.items():
            ax.plot(equity.index, equity.values, label=label, linewidth=1.5)
        ax.set_title(title, fontsize=14)
        ax.set_ylabel("Portfolio Value (normalised)")
        ax.set_xlabel("Date")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.xticks(rotation=30)
        ax.legend()
        ax.grid(True, alpha=0.4)
    return _save(fig, filename, out_dir)


def plot_drawdown(
    equity: pd.Series,
    title: str = "Drawdown",
    out_dir: Path = FIGURE_DIR,
    filename: str = "drawdown.pdf",
) -> Path:
    """Plot underwater (drawdown) chart."""
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max * 100  # in %
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.fill_between(drawdown.index, drawdown.values, 0,
                        color="crimson", alpha=0.5)
        ax.plot(drawdown.index, drawdown.values, color="crimson", linewidth=0.8)
        ax.set_title(title, fontsize=14)
        ax.set_ylabel("Drawdown (%)")
        ax.set_xlabel("Date")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.xticks(rotation=30)
        ax.grid(True, alpha=0.4)
    return _save(fig, filename, out_dir)


def plot_pred_vs_actual(
    y_true: pd.Series,
    y_pred: pd.Series,
    title: str = "Predicted vs. Actual Returns",
    out_dir: Path = FIGURE_DIR,
    filename: str = "pred_vs_actual.pdf",
) -> Path:
    """Scatter plot: predicted vs realised log-return."""
    with plt.style.context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Scatter
        axes[0].scatter(y_pred, y_true, alpha=0.3, s=10, color="steelblue")
        lims = [
            min(y_pred.min(), y_true.min()),
            max(y_pred.max(), y_true.max()),
        ]
        axes[0].plot(lims, lims, "r--", linewidth=1)
        axes[0].set_xlabel("Predicted")
        axes[0].set_ylabel("Actual")
        axes[0].set_title("Scatter")

        # Time-series overlay
        axes[1].plot(y_true.index, y_true.values, label="Actual",
                     alpha=0.7, linewidth=0.9)
        axes[1].plot(y_pred.index, y_pred.values, label="Predicted",
                     alpha=0.7, linewidth=0.9)
        axes[1].set_title("Time Series Overlay")
        axes[1].legend()
        axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.xticks(rotation=30)

        fig.suptitle(title, fontsize=14)
        plt.tight_layout()
    return _save(fig, filename, out_dir)


def plot_metric_comparison(
    metrics_df: pd.DataFrame,
    title: str = "Model Metric Comparison",
    out_dir: Path = FIGURE_DIR,
    filename: str = "metric_comparison.pdf",
) -> Path:
    """
    Bar chart comparing metrics across models / experiments.

    Parameters
    ----------
    metrics_df : DataFrame with index = model names, columns = metric names
    """
    with plt.style.context(STYLE):
        n_metrics = len(metrics_df.columns)
        fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 5))
        if n_metrics == 1:
            axes = [axes]
        for ax, col in zip(axes, metrics_df.columns):
            vals = metrics_df[col]
            bars = ax.bar(vals.index, vals.values, color="steelblue", alpha=0.8)
            ax.set_title(col)
            ax.set_xticklabels(vals.index, rotation=30, ha="right")
            for bar, val in zip(bars, vals.values):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() * 1.01,
                        f"{val:.3f}", ha="center", va="bottom", fontsize=9)
        fig.suptitle(title, fontsize=14)
        plt.tight_layout()
    return _save(fig, filename, out_dir)
