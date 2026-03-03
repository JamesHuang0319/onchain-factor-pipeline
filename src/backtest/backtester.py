"""
src/backtest/backtester.py
──────────────────────────────────────────────────────────────
Vectorised back-tester.

Trade execution model:
  - Signal on day t (from close[t] prediction)
  - Entry at open[t+1]  → avoids lookahead into close[t]
  - Exit  at open[t+2]  (hold 1 day) — for simplicity we use daily
    close returns scaled by signal; equivalent if hold period = 1 day.

Cost model:
  - Round-trip cost = cost_bps / 10_000 per TRADE (position change).
  - Turnover deducted only when position changes.

Outputs (all annualised assuming 365 calendar days):
  cumulative_return, annualised_return, annualised_volatility,
  max_drawdown, sharpe_ratio, turnover
"""
from __future__ import annotations

import numpy as np
import pandas as pd


TRADING_DAYS_YEAR = 365   # crypto trades 365 days


def _annualise(ret_daily: float, n_days: int) -> float:
    return (1 + ret_daily) ** (TRADING_DAYS_YEAR / n_days) - 1


def run_backtest(
    price_df: pd.DataFrame,
    signal: pd.Series,
    cost_bps: float = 10.0,
) -> dict:
    """
    Vectorised single-asset back-test.

    Parameters
    ----------
    price_df  : OHLCV DataFrame (UTC DatetimeIndex), at minimum needs 'close'.
    signal    : daily position series (0/+1/-1) aligned to price_df.index.
                Signal[t] is ESTABLISHED at close of t, ENTERED at open of t+1.
    cost_bps  : one-way transaction cost in basis points.

    Returns
    -------
    dict with performance metrics + daily equity Series.
    """
    # ── Align signal to price dates ───────────────────────────
    # De-duplicate index first (walk-forward concat may produce dups)
    signal = signal[~signal.index.duplicated(keep="last")]
    sig = signal.reindex(price_df.index).fillna(0.0)

    # ── Daily close-to-close log returns ─────────────────────
    # log_ret[t] = log(close[t] / close[t-1])
    log_ret = np.log(price_df["close"] / price_df["close"].shift(1))

    # ── Strategy daily log return ─────────────────────────────
    # Position held from t to t+1 is signal[t] entered on open[t+1].
    # Approximation: use log_ret[t+1] * signal[t] for daily P&L.
    # This is equivalent to: buy at close[t], sell at close[t+1].
    # NOTE: a slightly more accurate version would use open[t+1] →
    #       open[t+2] returns, but requires open data to be aligned.
    strat_ret = sig.shift(1) * log_ret   # shift(1): signal of yesterday

    # ── Transaction costs ─────────────────────────────────────
    # Turnover = |position_change|; cost applied each time position changes.
    position_change = sig.diff().abs()
    cost_per_trade = cost_bps / 10_000.0
    cost_series = position_change * cost_per_trade

    # Net strategy log return
    net_ret = strat_ret - cost_series

    # Drop leading NaN (first row of log_ret is always NaN)
    net_ret = net_ret.dropna()
    strat_ret_clean = strat_ret.reindex(net_ret.index)

    # ── Equity curve (cumulative) ─────────────────────────────
    equity = np.exp(net_ret.cumsum())

    # ── Max Drawdown ──────────────────────────────────────────
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_dd = float(drawdown.min())

    # ── Summary stats ─────────────────────────────────────────
    n = len(net_ret)
    total_log_ret  = float(net_ret.sum())
    ann_ret        = _annualise(np.exp(total_log_ret) - 1, n) if n > 0 else 0.0
    ann_vol        = float(net_ret.std() * np.sqrt(TRADING_DAYS_YEAR))
    sharpe         = ann_ret / ann_vol if ann_vol > 0 else 0.0
    turnover       = float(position_change.reindex(net_ret.index).mean())

    return {
        "cumulative_return":    float(equity.iloc[-1] - 1),
        "annualised_return":    ann_ret,
        "annualised_volatility": ann_vol,
        "max_drawdown":         max_dd,
        "sharpe_ratio":         sharpe,
        "turnover":             turnover,
        "cost_bps":             cost_bps,
        "n_days":               n,
        "equity":               equity,          # pd.Series for plotting
        "net_daily_ret":        net_ret,
    }


def sensitivity_analysis(
    price_df: pd.DataFrame,
    signal: pd.Series,
    cost_bps_list: list[float] = [5.0, 10.0, 20.0],
) -> pd.DataFrame:
    """
    Run backtest for multiple cost assumptions.

    Returns
    -------
    DataFrame: one row per cost_bps, columns = performance metrics.
    """
    rows = []
    for bps in cost_bps_list:
        res = run_backtest(price_df, signal, cost_bps=bps)
        row = {k: v for k, v in res.items() if k not in ("equity", "net_daily_ret")}
        rows.append(row)
    return pd.DataFrame(rows).set_index("cost_bps")
