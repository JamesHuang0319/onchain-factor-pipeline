"""
src/visualization/plotly_trading_chart.py
──────────────────────────────────────────────────────────────
Interactive trading-platform style chart (Plotly).

Chart layers:
  1. OHLC candlestick
  2. Predicted 7-day log-return overlay (right y-axis)
  3. Buy signals (triangle-up markers)
  4. Sell / exit signals (triangle-down markers)
  5. Optional: prediction confidence band (shaded area)

Exported as standalone HTML — viewable in any browser.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

TRADING_DIR = Path("reports/trading")


def make_trading_chart(
    price_df: pd.DataFrame,
    predictions: pd.Series,
    signal: pd.Series,
    symbol: str = "BTC-USD",
    model_name: str = "model",
    pred_std: Optional[pd.Series] = None,
    out_dir: Path = TRADING_DIR,
    filename: Optional[str] = None,
) -> Path:
    """
    Generate an interactive Plotly candlestick chart with predictions.

    Parameters
    ----------
    price_df    : OHLCV DataFrame (UTC DatetimeIndex)
    predictions : predicted 7-day log-return Series
    signal      : daily position signal (0/+1/-1)
    symbol      : asset name for title
    model_name  : model identifier for legend
    pred_std    : optional prediction std for confidence band
    out_dir     : directory to write HTML
    filename    : output filename; default auto-generated

    Returns
    -------
    Path to saved HTML file.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"{symbol.replace('-', '_')}_{model_name}_trading_chart.html"

    # ── Restrict to date range covered by predictions ─────────
    idx = predictions.index
    df = price_df.reindex(idx).dropna(subset=["open", "high", "low", "close"])
    pred_aligned = predictions.reindex(df.index)
    sig_aligned  = signal.reindex(df.index).fillna(0)

    # ── Buy / sell marker dates ───────────────────────────────
    buy_dates  = df.index[sig_aligned > 0]
    sell_dates = df.index[sig_aligned < 0]

    # ── Figure with 2 y-axes ──────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.03,
        subplot_titles=[f"{symbol} — Candlestick + Signals",
                        f"Predicted 7-day Log Return ({model_name})"],
    )

    # ── Candlestick ───────────────────────────────────────────
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLC",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # ── Buy signals ───────────────────────────────────────────
    if len(buy_dates) > 0:
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=df.loc[buy_dates, "low"] * 0.98,
                mode="markers",
                marker=dict(symbol="triangle-up", size=10, color="lime",
                            line=dict(width=1, color="green")),
                name="Long Signal",
            ),
            row=1, col=1,
        )

    # ── Sell / short signals ──────────────────────────────────
    if len(sell_dates) > 0:
        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=df.loc[sell_dates, "high"] * 1.02,
                mode="markers",
                marker=dict(symbol="triangle-down", size=10, color="red",
                            line=dict(width=1, color="darkred")),
                name="Short Signal",
            ),
            row=1, col=1,
        )

    # ── Prediction line ───────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=pred_aligned.index,
            y=pred_aligned.values,
            mode="lines",
            line=dict(color="royalblue", width=1.5),
            name="Pred. log-ret (7d)",
        ),
        row=2, col=1,
    )

    # ── Zero line on prediction panel ────────────────────────
    fig.add_hline(y=0, line_dash="dash", line_color="gray",
                  opacity=0.6, row=2, col=1)

    # ── Optional confidence band ──────────────────────────────
    if pred_std is not None:
        std_aligned = pred_std.reindex(df.index).fillna(0)
        fig.add_trace(
            go.Scatter(
                x=list(pred_aligned.index) + list(pred_aligned.index[::-1]),
                y=list((pred_aligned + std_aligned).values)
                  + list((pred_aligned - std_aligned).values[::-1]),
                fill="toself",
                fillcolor="rgba(65,105,225,0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                name="±1σ band",
                showlegend=True,
            ),
            row=2, col=1,
        )

    # ── Layout ────────────────────────────────────────────────
    fig.update_layout(
        height=750,
        title=dict(text=f"{symbol} Prediction & Trading Signals — {model_name}",
                   font=dict(size=18)),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Pred. Return", row=2, col=1)

    out_path = out_dir / filename
    fig.write_html(str(out_path), include_plotlyjs="cdn")
    return out_path
