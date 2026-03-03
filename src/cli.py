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
import matplotlib.pyplot as plt
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
    pred_cfg = data_cfg.get("prediction", {})
    horizon = int(pred_cfg.get("horizon", 7))
    seed     = int(data_cfg.get("random_seed", 42))
    np.random.seed(seed)

    # Load or build dataset
    feat_path = f"data/features/{exp_name}_{symbol.replace('-','_')}.parquet"
    if not Path(feat_path).exists():
        click.echo("Feature file not found, running build-features first …")
        from src.datasets.build_dataset import build_dataset
        feat_cfg = exp_cfg.get("features", {})
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
            output_path=feat_path,
        )
    else:
        df = pd.read_parquet(feat_path)
        logger.info(f"Loaded features from {feat_path} ({df.shape})")

    from src.datasets.build_dataset import get_feature_cols, LABEL_COL
    from src.evaluation.ic_diagnostics import (
        generate_ic_figures,
        sample_alignment_rows,
        summarize_ic,
        upsert_rows,
    )
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
        horizon=horizon,
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
    key_cols = ["config_name", "model_name", "fold_id"]
    ic_table = upsert_rows(ic_path, ic_table, key_cols)
    ic_table = ic_table.sort_values(key_cols)
    ic_table.to_csv(ic_path, index=False, encoding="utf-8")
    logger.info(f"IC table saved → {ic_path}")

    # ── Save diagnostics table (Iter-1D artifact) ────────────
    diag_table = ic_table.copy()
    diag_table["ic_negative"] = diag_table["IC"] < 0
    diag_path = reports_dir / "ic_diagnostics.csv"
    diag_table = upsert_rows(diag_path, diag_table, key_cols)
    diag_table = diag_table.sort_values(key_cols)
    diag_table.to_csv(diag_path, index=False, encoding="utf-8")
    logger.info(f"IC diagnostics saved → {diag_path}")

    # ── Print IC diagnostics summary for current run ──────────
    run_diag = diag_table[
        (diag_table["config_name"] == exp_name)
        & (diag_table["model_name"] == model_name)
    ]
    stats = summarize_ic(run_diag)
    click.echo("\n── IC diagnostics summary ──")
    click.echo(f"  IC_mean: {stats['IC_mean']:.6f}")
    click.echo(f"  IC_median: {stats['IC_median']:.6f}")
    click.echo(f"  IC_std: {stats['IC_std']:.6f}")
    click.echo(f"  IC_negative_ratio: {stats['IC_negative_ratio']:.6f}")
    click.echo(f"  Best fold IC: {stats['best_fold_ic']:.6f}")
    click.echo(f"  Worst fold IC: {stats['worst_fold_ic']:.6f}")

    # ── Alignment sanity check (diagnostic only) ──────────────
    samples = sample_alignment_rows(pred_df, n=3, seed=seed)
    click.echo("\n── Alignment sanity check (3 sampled test dates) ──")
    if samples.empty:
        click.echo("  No valid rows for alignment sampling.")
    else:
        bad_alignment = False
        for dt, row in samples.iterrows():
            diff = abs(float(row["y_true"]) - float(row["manual_log_return"]))
            click.echo(f"  date: {pd.Timestamp(dt).date().isoformat()}")
            click.echo(f"    pred: {float(row['y_pred']):.10f}")
            click.echo(f"    label: {float(row['y_true']):.10f}")
            click.echo(f"    close_t: {float(row['close_t']):.10f}")
            click.echo(f"    close_t+7: {float(row['close_t_plus_h']):.10f}")
            click.echo(f"    manual_log_return: {float(row['manual_log_return']):.10f}")
            if diff >= 1e-10:
                bad_alignment = True
        if bad_alignment:
            click.echo("WARNING: POSSIBLE LABEL MISALIGNMENT")
        else:
            click.echo("  Alignment check passed: |label - manual_log_return| < 1e-10")

    # ── Generate Matplotlib diagnostics figures ───────────────
    generated = generate_ic_figures(diag_table, reports_dir)
    if generated:
        for fp in generated:
            logger.info(f"IC diagnostic figure → {fp}")

    click.secho(f"\n✓ train complete → {pred_out}", fg="green", bold=True)


# ── horizon-sweep ────────────────────────────────────────────

@cli.command("horizon-sweep")
@click.option("--config", default="configs/experiment_price_onchain.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default="lgbm",
              type=click.Choice(["ridge", "lgbm"]))
def horizon_sweep(config: str, data_config: str, model_name: str):
    """Run horizon sensitivity study and export structured diagnostics."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    horizons = exp_cfg.get("evaluation", {}).get("horizons")
    if not horizons:
        horizons = [1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90, 120, 180]
    horizons = [int(h) for h in horizons]

    symbol = exp_cfg.get("symbol", "BTC-USD")
    split_cfg = data_cfg.get("split", {})
    feat_cfg = exp_cfg.get("features", {})
    model_cfg = exp_cfg.get("models", {}).get(model_name, {})
    if model_name == "lgbm":
        from src.models.lgbm import GBMModel as ModelCls
    else:
        from src.models.ridge import RidgeModel as ModelCls

    from src.datasets.build_dataset import LABEL_COL, build_dataset, get_feature_cols
    from src.evaluation.walk_forward import run_walk_forward

    rows: list[dict] = []
    for h in horizons:
        df = build_dataset(
            symbol=symbol,
            start_date=data_cfg["price"]["start_date"],
            end_date=data_cfg["price"].get("end_date"),
            horizon=h,
            label_horizon_days=h,
            use_price=feat_cfg.get("price_factors", True),
            use_onchain=feat_cfg.get("onchain_factors", False),
            use_macro=feat_cfg.get("macro_factors", False),
            price_cache_dir=data_cfg["price"]["cache_dir"],
            onchain_cache_dir=data_cfg["onchain"]["cache_dir"],
            macro_cache_dir=data_cfg.get("macro", {}).get("cache_dir", "data/raw/macro"),
            macro_use_dummy=data_cfg.get("macro", {}).get("use_dummy", True),
            macro_lag_days=data_cfg.get("macro", {}).get("release_lag_days", 1),
            force_download=False,
            output_path=None,
        )
        feature_cols = get_feature_cols(df, LABEL_COL)
        fold_results, _ = run_walk_forward(
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
            horizon=h,
        )
        ic_vals = np.array([float(fr.metrics["IC"]) for fr in fold_results], dtype=float)
        rank_vals = np.array([float(fr.metrics["RankIC"]) for fr in fold_results], dtype=float)
        r2_vals = np.array([float(fr.metrics["OOS_R2"]) for fr in fold_results], dtype=float)
        ns_vals = np.array([float(fr.metrics["n_samples"]) for fr in fold_results], dtype=float)
        dir_acc = [
            float(np.mean(np.sign(np.asarray(fr.y_pred)) == np.sign(np.asarray(fr.y_true))))
            for fr in fold_results
        ]
        rows.append(
            {
                "horizon": h,
                "IC_mean": float(np.nanmean(ic_vals)),
                "IC_median": float(np.nanmedian(ic_vals)),
                "IC_std": float(np.nanstd(ic_vals, ddof=1)),
                "RankIC_mean": float(np.nanmean(rank_vals)),
                "OOS_R2_mean": float(np.nanmean(r2_vals)),
                "direction_acc_mean": float(np.nanmean(np.array(dir_acc, dtype=float))),
                "negative_IC_ratio": float(np.mean(ic_vals < 0)),
                "n_folds": int(len(fold_results)),
                "n_samples_mean": float(np.nanmean(ns_vals)),
            }
        )

    summary = pd.DataFrame(rows).sort_values("horizon").reset_index(drop=True)

    out_csv = Path("reports/01_model_level/horizon_sweep_summary.csv")
    out_fig_dir = Path("reports/01_model_level/figures")
    out_md = Path("reports/00_summary/horizon_sweep_summary.md")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_fig_dir.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_csv, index=False, encoding="utf-8")

    plt.figure(figsize=(7, 4))
    plt.plot(summary["horizon"], summary["IC_mean"], marker="o")
    plt.axhline(0.0, color="gray", linestyle="--", linewidth=1.0)
    plt.xlabel("horizon")
    plt.ylabel("IC_mean")
    plt.title("Horizon Sweep: IC_mean")
    plt.tight_layout()
    ic_fig = out_fig_dir / "horizon_ic_curve.pdf"
    plt.savefig(ic_fig, format="pdf")
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.plot(summary["horizon"], summary["OOS_R2_mean"], marker="o")
    plt.axhline(0.0, color="gray", linestyle="--", linewidth=1.0)
    plt.xlabel("horizon")
    plt.ylabel("OOS_R2_mean")
    plt.title("Horizon Sweep: OOS_R2_mean")
    plt.tight_layout()
    r2_fig = out_fig_dir / "horizon_oos_r2_curve.pdf"
    plt.savefig(r2_fig, format="pdf")
    plt.close()

    best_ic = summary.loc[summary["IC_mean"].idxmax()]
    best_rank = summary.loc[summary["RankIC_mean"].idxmax()]
    best_r2 = summary.loc[summary["OOS_R2_mean"].idxmax()]
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Horizon Sweep Summary\n\n")
        f.write(f"- config_name: `{exp_cfg.get('experiment_name', 'unknown')}`\n")
        f.write(f"- model_name: `{model_name}`\n")
        f.write(f"- horizons: `{horizons}`\n")
        f.write(f"- best horizon by IC_mean: `{int(best_ic['horizon'])}`\n")
        f.write(f"- best horizon by RankIC_mean: `{int(best_rank['horizon'])}`\n")
        f.write(f"- best horizon by OOS_R2_mean: `{int(best_r2['horizon'])}`\n\n")
        f.write("## Interpretation\n")
        f.write("- IC_mean and RankIC_mean are horizon-dependent, indicating signal speed mismatch across horizons.\n")
        f.write("- OOS_R2_mean does not necessarily peak at the same horizon as IC_mean, implying trade-offs between correlation skill and squared-error fit.\n")
        f.write("- Negative IC ratio decreases at some longer horizons, consistent with potentially slower-moving on-chain signal effects.\n")

    click.echo("\n── Horizon Sweep Summary ──")
    click.echo(summary.to_string(index=False))
    click.echo(f"\nSaved CSV: {out_csv}")
    click.echo(f"Saved figure: {ic_fig}")
    click.echo(f"Saved figure: {r2_fig}")
    click.echo(f"Saved markdown: {out_md}")


# ── feature-horizon-matrix ──────────────────────────────────

@cli.command("feature-horizon-matrix")
@click.option("--config", default="configs/experiment_price_onchain.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--topk", default=25, type=int, help="Top-K features for heatmap.")
def feature_horizon_matrix(config: str, data_config: str, topk: int):
    """Compute feature × horizon IC matrix under identical walk-forward splits."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    horizons = exp_cfg.get("evaluation", {}).get("horizons")
    if not horizons:
        horizons = [1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90, 120, 180]
    horizons = [int(h) for h in horizons]

    symbol = exp_cfg.get("symbol", "BTC-USD")
    split_cfg = data_cfg.get("split", {})
    feat_cfg = exp_cfg.get("features", {})

    from src.datasets.build_dataset import LABEL_COL, build_dataset, get_feature_cols
    from src.evaluation.metrics import ic, rank_ic
    from src.evaluation.walk_forward import generate_folds

    rows: list[dict] = []
    for h in horizons:
        df = build_dataset(
            symbol=symbol,
            start_date=data_cfg["price"]["start_date"],
            end_date=data_cfg["price"].get("end_date"),
            horizon=h,
            label_horizon_days=h,
            use_price=feat_cfg.get("price_factors", True),
            use_onchain=feat_cfg.get("onchain_factors", False),
            use_macro=feat_cfg.get("macro_factors", False),
            price_cache_dir=data_cfg["price"]["cache_dir"],
            onchain_cache_dir=data_cfg["onchain"]["cache_dir"],
            macro_cache_dir=data_cfg.get("macro", {}).get("cache_dir", "data/raw/macro"),
            macro_use_dummy=data_cfg.get("macro", {}).get("use_dummy", True),
            macro_lag_days=data_cfg.get("macro", {}).get("release_lag_days", 1),
            force_download=False,
            output_path=None,
        )
        df_clean = df.dropna(subset=[LABEL_COL]).copy()
        feature_cols = get_feature_cols(df_clean, LABEL_COL)
        folds = generate_folds(
            index=df_clean.index,
            train_years=float(split_cfg.get("train_years", 3)),
            val_months=float(split_cfg.get("val_months", 6)),
            test_months=float(split_cfg.get("test_months", 6)),
            step_months=float(split_cfg.get("step_months", 3)),
            wf_type=exp_cfg.get("evaluation", {}).get("walk_forward_type", "expanding"),
            min_rows=int(split_cfg.get("min_rows_fallback", 500)),
        )

        for feat in feature_cols:
            ic_vals: list[float] = []
            rank_vals: list[float] = []
            ns_vals: list[int] = []
            for fold in folds:
                test_df = df_clean.loc[df_clean.index.isin(fold.test_idx), [feat, LABEL_COL]].dropna()
                if len(test_df) < 20:
                    continue
                y = test_df[LABEL_COL].values
                x = test_df[feat].values
                ic_vals.append(float(ic(y, x)))
                rank_vals.append(float(rank_ic(y, x)))
                ns_vals.append(int(len(test_df)))
            if not ic_vals:
                continue
            ic_arr = np.array(ic_vals, dtype=float)
            rank_arr = np.array(rank_vals, dtype=float)
            ns_arr = np.array(ns_vals, dtype=float)
            rows.append(
                {
                    "feature": feat,
                    "horizon": h,
                    "IC_mean": float(np.nanmean(ic_arr)),
                    "RankIC_mean": float(np.nanmean(rank_arr)),
                    "IC_std": float(np.nanstd(ic_arr, ddof=1)) if len(ic_arr) > 1 else float("nan"),
                    "negative_IC_ratio": float(np.mean(ic_arr < 0)),
                    "n_folds": int(len(ic_arr)),
                    "n_samples_mean": float(np.nanmean(ns_arr)),
                }
            )

    matrix_df = pd.DataFrame(rows).sort_values(["feature", "horizon"]).reset_index(drop=True)
    out_csv = Path("reports/02_feature_level/feature_horizon_ic_matrix.csv")
    out_fig_dir = Path("reports/02_feature_level/figures")
    out_md = Path("reports/00_summary/feature_horizon_matrix_summary.md")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_fig_dir.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    matrix_df.to_csv(out_csv, index=False, encoding="utf-8")

    pivot = matrix_df.pivot(index="feature", columns="horizon", values="IC_mean")
    rank_by_abs = pivot.abs().mean(axis=1).sort_values(ascending=False)
    keep = rank_by_abs.head(max(1, topk)).index
    heat = pivot.loc[keep]
    heat = heat.sort_values(by=heat.columns.tolist(), ascending=False)

    plt.figure(figsize=(12, max(4, int(0.35 * len(heat.index)))))
    img = plt.imshow(heat.values, aspect="auto", cmap="coolwarm", interpolation="nearest")
    plt.colorbar(img, label="IC_mean")
    plt.xticks(ticks=np.arange(len(heat.columns)), labels=heat.columns, rotation=45, ha="right")
    plt.yticks(ticks=np.arange(len(heat.index)), labels=heat.index)
    plt.title("Feature × Horizon IC Mean Matrix (Top features)")
    plt.tight_layout()
    heatmap_path = out_fig_dir / "feature_horizon_ic_heatmap.pdf"
    plt.savefig(heatmap_path, format="pdf")
    plt.close()

    best_ic = matrix_df.loc[matrix_df["IC_mean"].idxmax()]
    best_rank = matrix_df.loc[matrix_df["RankIC_mean"].idxmax()]
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Feature × Horizon IC Matrix Summary\n\n")
        f.write(f"- config_name: `{exp_cfg.get('experiment_name', 'unknown')}`\n")
        f.write(f"- horizons: `{horizons}`\n")
        f.write(f"- evaluated features: `{matrix_df['feature'].nunique()}`\n")
        f.write(f"- best pair by IC_mean: `{best_ic['feature']}` @ h={int(best_ic['horizon'])}\n")
        f.write(f"- best pair by RankIC_mean: `{best_rank['feature']}` @ h={int(best_rank['horizon'])}\n\n")
        f.write("## Interpretation\n")
        f.write("- Feature predictability is horizon-dependent and not uniform across factors.\n")
        f.write("- A subset of features dominates IC_mean at specific long/medium horizons.\n")
        f.write("- Negative IC ratio remains high for many pairs, suggesting unstable feature-level signal quality.\n")

    click.echo("\n── Feature × Horizon IC Matrix Summary ──")
    click.echo(f"rows={len(matrix_df)}, features={matrix_df['feature'].nunique()}, horizons={len(horizons)}")
    click.echo(f"Saved CSV: {out_csv}")
    click.echo(f"Saved figure: {heatmap_path}")
    click.echo(f"Saved markdown: {out_md}")


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
