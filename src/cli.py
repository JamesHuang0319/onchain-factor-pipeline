"""
src/cli.py
──────────────────────────────────────────────────────────────
Command-line interface (Click) for the crypto-predict pipeline.

Commands:
  download-data   – fetch price + on-chain data (cached)
  build-features  – build feature dataset, save to data/features/
  train           – run walk-forward training, save models + predictions
  backtest        – run backtest on saved predictions, print perf table
  report          – generate all figures + summary report
  validate        – run leakage guard checks (fail fast on any violation)

Example (3-command demo):
  python -m src.cli download-data --config configs/experiment_price_only.yaml
  python -m src.cli train          --config configs/experiment_price_only.yaml
  python -m src.cli report         --config configs/experiment_price_only.yaml
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
import numpy as np
import pandas as pd
import yaml


def _force_utf8_runtime() -> None:
    """Harden CLI runtime encoding on Windows before any file IO."""
    if os.name == "nt":
        os.environ.setdefault("PYTHONUTF8", "1")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")


_force_utf8_runtime()

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cli")

# ── Helpers ───────────────────────────────────────────────────

def _load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        return yaml.safe_load(f)


def _load_data_cfg(data_cfg_path: str = "configs/data.yaml") -> dict:
    return _load_yaml(data_cfg_path)


def _load_exp_cfg(config: str) -> dict:
    return _load_yaml(config)


def _resolve_model(model_name: str, model_cfg: dict):
    """Return (ModelClass, config_dict) for a given model name."""
    if model_name == "ridge":
        from src.models.ridge import RidgeModel
        return RidgeModel, model_cfg.get("ridge", {})
    elif model_name in ("lgbm", "gbm", "xgboost"):
        from src.models.lgbm import GBMModel
        return GBMModel, model_cfg.get("lgbm", {})
    else:
        raise ValueError(f"Unknown model: {model_name}")


# ── CLI group ─────────────────────────────────────────────────

@click.group()
def cli():
    """Crypto price prediction & backtesting pipeline."""
    pass


# ── download-data ─────────────────────────────────────────────

@cli.command("download-data")
@click.option("--config", default="configs/experiment_price_only.yaml",
              help="Experiment config YAML path.")
@click.option("--data-config", default="configs/data.yaml",
              help="Data sources config YAML path.")
@click.option("--force", is_flag=True, default=False,
              help="Force re-download, bypass cache.")
def download_data(config: str, data_config: str, force: bool):
    """Download price and on-chain data (cached to data/raw/)."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    symbol     = exp_cfg.get("symbol", "BTC-USD")
    start      = data_cfg["price"]["start_date"]
    end        = data_cfg["price"].get("end_date")
    price_dir  = data_cfg["price"]["cache_dir"]
    onchain_dir= data_cfg["onchain"]["cache_dir"]
    use_onchain= exp_cfg.get("features", {}).get("onchain_factors", False)

    # Price
    from src.ingest.price import download_price
    logger.info(f"Downloading price data for {symbol} …")
    df = download_price(symbol, start, end, price_dir, force)
    logger.info(f"  ✓ Price: {len(df)} rows ({df.index[0].date()} → {df.index[-1].date()})")

    # On-chain (Iter-1+)
    if use_onchain:
        from src.ingest.onchain import load_onchain
        metrics = data_cfg["onchain"]["metrics"]
        logger.info(f"Downloading on-chain metrics: {metrics} …")
        oc = load_onchain(metrics=metrics, cache_dir=onchain_dir, force=force)
        logger.info(f"  ✓ On-chain: {len(oc)} rows, {oc.shape[1]} metrics")

    click.secho("✓ download-data complete.", fg="green", bold=True)


# ── build-features ────────────────────────────────────────────

@cli.command("build-features")
@click.option("--config", default="configs/experiment_price_only.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--force", is_flag=True, default=False)
def build_features(config: str, data_config: str, force: bool):
    """Build feature + label dataset, save to data/features/."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    exp_name    = exp_cfg["experiment_name"]
    symbol      = exp_cfg.get("symbol", "BTC-USD")
    feat_cfg    = exp_cfg.get("features", {})
    pred_cfg    = data_cfg.get("prediction", {})
    horizon     = int(pred_cfg.get("horizon", 7))

    out_path = f"data/features/{exp_name}_{symbol.replace('-','_')}.parquet"

    from src.datasets.build_dataset import build_dataset
    df = build_dataset(
        symbol=symbol,
        start_date=data_cfg["price"]["start_date"],
        end_date=data_cfg["price"].get("end_date"),
        horizon=horizon,
        use_price=feat_cfg.get("price_factors", True),
        use_onchain=feat_cfg.get("onchain_factors", False),
        use_macro=feat_cfg.get("macro_factors", False),
        price_cache_dir=data_cfg["price"]["cache_dir"],
        onchain_cache_dir=data_cfg["onchain"]["cache_dir"],
        macro_use_dummy=data_cfg.get("macro", {}).get("use_dummy", True),
        macro_lag_days=data_cfg.get("macro", {}).get("release_lag_days", 1),
        force_download=force,
        output_path=out_path,
    )
    logger.info(f"Dataset shape: {df.shape}")
    click.secho(f"✓ build-features complete → {out_path}", fg="green", bold=True)


# ── train ─────────────────────────────────────────────────────

@cli.command("train")
@click.option("--config", default="configs/experiment_price_only.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default="lgbm",
              type=click.Choice(["ridge", "lgbm"]), help="Model to train.")
def train(config: str, data_config: str, model_name: str):
    """Run walk-forward training and save predictions."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    exp_name = exp_cfg["experiment_name"]
    symbol   = exp_cfg.get("symbol", "BTC-USD")
    split_cfg= data_cfg.get("split", {})
    seed     = int(data_cfg.get("random_seed", 42))
    np.random.seed(seed)

    # Load or build dataset
    feat_path = f"data/features/{exp_name}_{symbol.replace('-','_')}.parquet"
    if not Path(feat_path).exists():
        click.echo("Feature file not found, running build-features first …")
        from src.datasets.build_dataset import build_dataset
        feat_cfg = exp_cfg.get("features", {})
        pred_cfg = data_cfg.get("prediction", {})
        df = build_dataset(
            symbol=symbol,
            start_date=data_cfg["price"]["start_date"],
            end_date=data_cfg["price"].get("end_date"),
            horizon=int(pred_cfg.get("horizon", 7)),
            use_price=feat_cfg.get("price_factors", True),
            use_onchain=feat_cfg.get("onchain_factors", False),
            use_macro=feat_cfg.get("macro_factors", False),
            price_cache_dir=data_cfg["price"]["cache_dir"],
            onchain_cache_dir=data_cfg["onchain"]["cache_dir"],
            macro_use_dummy=data_cfg.get("macro", {}).get("use_dummy", True),
            macro_lag_days=data_cfg.get("macro", {}).get("release_lag_days", 1),
            output_path=feat_path,
        )
    else:
        df = pd.read_parquet(feat_path)
        logger.info(f"Loaded features from {feat_path} ({df.shape})")

    from src.datasets.build_dataset import get_feature_cols, LABEL_COL
    from src.evaluation.walk_forward import fold_results_to_table, run_walk_forward
    from src.evaluation.metrics import compute_metrics, rank_ic

    feature_cols = get_feature_cols(df, LABEL_COL)
    logger.info(f"Feature count: {len(feature_cols)}")

    ModelCls, model_cfg = _resolve_model(model_name, exp_cfg.get("models", {}))

    fold_results, pred_df = run_walk_forward(
        df=df,
        feature_cols=feature_cols,
        label_col=LABEL_COL,
        model_cls=ModelCls,
        model_config=model_cfg,
        train_years=float(split_cfg.get("train_years", 3)),
        val_months=float(split_cfg.get("val_months", 6)),
        test_months=float(split_cfg.get("test_months", 6)),
        step_months=float(split_cfg.get("step_months", 3)),
        wf_type=exp_cfg.get("evaluation", {}).get("walk_forward_type", "expanding"),
        min_rows=int(split_cfg.get("min_rows_fallback", 500)),
    )

    # ── Aggregate metrics ──────────────────────────────────────
    all_metrics = compute_metrics(
        pred_df["y_true"].values,
        pred_df["y_pred"].values,
        prefix=f"{model_name}_oos",
    )
    ric = rank_ic(pred_df["y_true"].values, pred_df["y_pred"].values)
    all_metrics[f"{model_name}_oos_rank_ic"] = ric

    click.echo("\n── Out-of-sample metrics ──")
    for k, v in all_metrics.items():
        click.echo(f"  {k}: {v:.4f}")

    # ── Save predictions ───────────────────────────────────────
    pred_out = f"data/features/{exp_name}_{symbol.replace('-','_')}_{model_name}_preds.parquet"
    pred_df.to_parquet(pred_out)
    logger.info(f"Predictions saved → {pred_out}")

    # ── Save metrics ───────────────────────────────────────────
    metrics_out = f"data/features/{exp_name}_{model_name}_metrics.json"
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)

    # ── Save per-fold IC table (Iter-1C artifact) ─────────────
    ic_table = fold_results_to_table(
        fold_results=fold_results,
        config_name=exp_name,
        model_name=model_name,
    )
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    ic_path = reports_dir / "ic_table.csv"
    if ic_path.exists():
        prev = pd.read_csv(ic_path)
        key_cols = ["config_name", "model_name", "fold_id"]
        current_keys = set(
            tuple(x) for x in ic_table[key_cols].astype(str).to_numpy()
        )
        prev = prev[
            ~prev[key_cols].astype(str).apply(tuple, axis=1).isin(current_keys)
        ]
        ic_table = pd.concat([prev, ic_table], ignore_index=True)
    ic_table = ic_table.sort_values(["config_name", "model_name", "fold_id"])
    ic_table.to_csv(ic_path, index=False, encoding="utf-8")
    logger.info(f"IC table saved → {ic_path}")

    click.secho(f"\n✓ train complete → {pred_out}", fg="green", bold=True)


# ── backtest ──────────────────────────────────────────────────

@cli.command("backtest")
@click.option("--config", default="configs/experiment_price_only.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default="lgbm",
              type=click.Choice(["ridge", "lgbm"]))
def backtest(config: str, data_config: str, model_name: str):
    """Run backtest on saved predictions and print performance table."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    exp_name    = exp_cfg["experiment_name"]
    symbol      = exp_cfg.get("symbol", "BTC-USD")
    strat_cfg   = exp_cfg.get("strategy", {})
    cost_list   = strat_cfg.get("cost_bps", [5, 10, 20])

    pred_path = f"data/features/{exp_name}_{symbol.replace('-','_')}_{model_name}_preds.parquet"
    if not Path(pred_path).exists():
        click.secho(f"Prediction file not found: {pred_path}\nRun 'train' first.", fg="red")
        sys.exit(1)

    pred_df = pd.read_parquet(pred_path)

    # Load price data for backtest returns
    from src.ingest.price import download_price
    from src.etl.cleaner import clean_price
    price_raw = download_price(
        symbol,
        data_cfg["price"]["start_date"],
        data_cfg["price"].get("end_date"),
        data_cfg["price"]["cache_dir"],
        force=False,
    )
    price_df = clean_price(price_raw)

    from src.backtest.strategy import make_signal
    from src.backtest.backtester import sensitivity_analysis, run_backtest

    predictions = pred_df["y_pred"]
    signal = make_signal(
        predictions,
        mode=strat_cfg.get("mode", "long_only"),
        top_quantile=float(strat_cfg.get("top_quantile", 0.2)),
        bottom_quantile=float(strat_cfg.get("bottom_quantile", 0.2)),
    )

    sensitivity_df = sensitivity_analysis(price_df, signal, cost_bps_list=cost_list)
    click.echo(f"\n── Backtest Sensitivity (symbol={symbol}, model={model_name}) ──")
    click.echo(sensitivity_df.to_string())

    # Save equity curve for default cost
    default_bps = float(strat_cfg.get("default_cost_bps", 10))
    result = run_backtest(price_df, signal, cost_bps=default_bps)
    equity = result["equity"]
    equity_path = f"data/features/{exp_name}_{model_name}_equity.parquet"
    equity.to_frame("equity").to_parquet(equity_path)

    click.secho(f"\n✓ backtest complete (equity → {equity_path})", fg="green", bold=True)


# ── report ────────────────────────────────────────────────────

@cli.command("report")
@click.option("--config", default="configs/experiment_price_only.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default="lgbm",
              type=click.Choice(["ridge", "lgbm"]))
def report(config: str, data_config: str, model_name: str):
    """Generate all figures and write summary HTML report."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    exp_name = exp_cfg["experiment_name"]
    symbol   = exp_cfg.get("symbol", "BTC-USD")
    fig_dir  = Path(exp_cfg.get("output", {}).get("figures_dir", "reports/figures"))
    trd_dir  = Path(exp_cfg.get("output", {}).get("trading_dir", "reports/trading"))
    strat_cfg = exp_cfg.get("strategy", {})

    # ── Load predictions ───────────────────────────────────────
    pred_path = f"data/features/{exp_name}_{symbol.replace('-','_')}_{model_name}_preds.parquet"
    equity_path = f"data/features/{exp_name}_{model_name}_equity.parquet"

    if not Path(pred_path).exists():
        click.secho("Run 'train' and 'backtest' first.", fg="red"); sys.exit(1)

    pred_df = pd.read_parquet(pred_path)
    y_true  = pred_df["y_true"]
    y_pred  = pred_df["y_pred"]

    # ── Load price ─────────────────────────────────────────────
    from src.ingest.price import download_price
    from src.etl.cleaner import clean_price
    price_df = clean_price(download_price(
        symbol, data_cfg["price"]["start_date"],
        data_cfg["price"].get("end_date"), data_cfg["price"]["cache_dir"]
    ))

    # ── Matplotlib static figures ──────────────────────────────
    from src.visualization.matplotlib_reports import (
        plot_equity_curves, plot_drawdown, plot_pred_vs_actual,
    )

    if Path(equity_path).exists():
        equity = pd.read_parquet(equity_path)["equity"]
        eq_path  = plot_equity_curves({model_name: equity}, out_dir=fig_dir,
                                      filename=f"{exp_name}_{model_name}_equity.pdf")
        dd_path  = plot_drawdown(equity, out_dir=fig_dir,
                                 filename=f"{exp_name}_{model_name}_drawdown.pdf")
        logger.info(f"Equity → {eq_path}")
        logger.info(f"Drawdown → {dd_path}")

    pa_path = plot_pred_vs_actual(y_true, y_pred, out_dir=fig_dir,
                                  filename=f"{exp_name}_{model_name}_pred_vs_actual.pdf")
    logger.info(f"Pred vs Actual → {pa_path}")

    # ── Plotly interactive chart ───────────────────────────────
    from src.backtest.strategy import make_signal
    from src.visualization.plotly_trading_chart import make_trading_chart

    signal = make_signal(
        y_pred,
        mode=strat_cfg.get("mode", "long_only"),
        top_quantile=float(strat_cfg.get("top_quantile", 0.2)),
        bottom_quantile=float(strat_cfg.get("bottom_quantile", 0.2)),
    )
    html_path = make_trading_chart(
        price_df=price_df,
        predictions=y_pred,
        signal=signal,
        symbol=symbol,
        model_name=model_name,
        out_dir=trd_dir,
    )
    logger.info(f"Plotly chart → {html_path}")

    # ── Load metrics ───────────────────────────────────────────
    metrics_path = f"data/features/{exp_name}_{model_name}_metrics.json"
    metrics = {}
    if Path(metrics_path).exists():
        with open(metrics_path, encoding="utf-8") as f:
            metrics = json.load(f)

    # ── Write markdown summary ─────────────────────────────────
    feat_path = f"data/features/{exp_name}_{symbol.replace('-','_')}.parquet"
    n_feat = 0
    if Path(feat_path).exists():
        from src.datasets.build_dataset import get_feature_cols, LABEL_COL
        tmp = pd.read_parquet(feat_path)
        n_feat = len(get_feature_cols(tmp, LABEL_COL))

    Path("reports").mkdir(exist_ok=True)
    summary_path = Path("reports/summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Crypto Predict — Summary Report\n\n")
        f.write(f"**Experiment**: `{exp_name}`  \n")
        f.write(f"**Symbol**: `{symbol}`  \n")
        f.write(f"**Model**: `{model_name}`  \n")
        f.write(f"**Feature count**: {n_feat}  \n\n")
        f.write("## Out-of-Sample Metrics\n\n| Metric | Value |\n|---|---|\n")
        for k, v in metrics.items():
            f.write(f"| {k} | {v:.4f} |\n")
        f.write("\n## Outputs\n\n")
        f.write(f"- [Plotly Trading Chart]({html_path.relative_to('.')})\n")
        f.write(f"- Figures: `{fig_dir}/`\n")

    click.secho(f"\n✓ report complete → {summary_path}", fg="green", bold=True)
    click.echo(f"  Plotly chart : {html_path}")
    click.echo(f"  Figures dir  : {fig_dir}/")


# ── validate ─────────────────────────────────────────────────

@cli.command("validate")
@click.option("--config", default="configs/experiment_price_only.yaml")
@click.option("--data-config", default="configs/data.yaml")
def validate(config: str, data_config: str):
    """Run leakage guard checks. Exits with code 1 if violations found."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    exp_name = exp_cfg["experiment_name"]
    symbol   = exp_cfg.get("symbol", "BTC-USD")
    feat_path = f"data/features/{exp_name}_{symbol.replace('-','_')}.parquet"

    if not Path(feat_path).exists():
        click.secho("Feature file not found, building …", fg="yellow")
        feat_cfg = exp_cfg.get("features", {})
        from src.datasets.build_dataset import build_dataset
        build_dataset(
            symbol=symbol,
            start_date=data_cfg["price"]["start_date"],
            use_price=feat_cfg.get("price_factors", True),
            use_onchain=feat_cfg.get("onchain_factors", False),
            use_macro=feat_cfg.get("macro_factors", False),
            price_cache_dir=data_cfg["price"]["cache_dir"],
            onchain_cache_dir=data_cfg["onchain"]["cache_dir"],
            output_path=feat_path,
        )

    df = pd.read_parquet(feat_path)
    from src.datasets.build_dataset import assert_no_leakage, LABEL_COL
    try:
        assert_no_leakage(df, label_col=LABEL_COL)
        click.secho("✓ No leakage detected.", fg="green", bold=True)
    except AssertionError as e:
        click.secho(str(e), fg="red", bold=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
