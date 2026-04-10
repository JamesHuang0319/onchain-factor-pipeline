"""
src/cli.py
Main CLI entrypoint for the BTC on-chain prediction pipeline.

Command groups:
  Data:
    download-data, build-features, data-audit, predict-latest
  Safety / validation:
    validate, test-full-history
  Training / selection:
    show-search-space, tune, train, horizon-sweep, feature-horizon-matrix
  Backtest / reporting:
    backtest, report, halving-strategy-study
  Experiment aggregation:
    experiment-summary, latest-prediction-report

Typical workflow:
  1. python -m src.cli download-data --config configs/experiment.yaml
  2. python -m src.cli build-features --config configs/experiment.yaml
  3. python -m src.cli tune --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
  4. python -m src.cli train --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
  5. python -m src.cli backtest --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
  6. python -m src.cli report --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain

Key output locations:
  data/features/                  model metrics, predictions, equity curves
  models_saved/                   final fitted models for reuse / latest inference
  reports/experiments/            per-run figures, charts, markdown summaries
  reports/summary/                aggregated tables, tuning tables, stability studies
  reports/demos/                  copied showcase-ready figures and charts

Common selector semantics:
  --model
    ML: ridge, lasso, svm, rf, lgbm, xgboost
    DL: lstm, cnn_lstm, gru, tcn
  --task
    classification: predict next-day direction_h
    regression: predict next-day log_ret_h
  --dataset-variant
    onchain         raw on-chain factors only
    ta              price / TA / calendar-style features
    all             full feature set
    boruta_onchain  screened on-chain factors
    boruta_ta       screened TA-side features
    boruta_all      screened full feature set
    univariate      single close-price baseline

Practical rule of thumb:
  Use --help to see common choices quickly.
  Use show-search-space when you need the detailed tuning candidate set.
"""

from __future__ import annotations

import copy
import json
import inspect
import logging
import os
import random
import re
import subprocess
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
        os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
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

# ── Common CLI choices / help text ───────────────────────────
# These constants are reused in command help so users can learn the
# common model / task / feature-subset choices without opening YAML.

TASK_CHOICES = ["classification", "regression"]
DATASET_VARIANTS = [
    "onchain",
    "ta",
    "all",
    "boruta_onchain",
    "boruta_ta",
    "boruta_all",
    "univariate",
]
MODEL_HELP_TEXT = (
    "Model name. Common choices: ridge, lasso, svm, rf, lgbm, xgboost, "
    "lstm, cnn_lstm, gru, tcn."
)
TASK_HELP_TEXT = "Task name. Choices: classification, regression."
DATASET_VARIANT_HELP_TEXT = (
    "Feature subset. Choices: onchain, ta, all, boruta_onchain, "
    "boruta_ta, boruta_all, univariate."
)

# ── Helpers ───────────────────────────────────────────────────

def _load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        return yaml.safe_load(f)


def _load_data_cfg(data_cfg_path: str = "configs/data.yaml") -> dict:
    return _load_yaml(data_cfg_path)


def _load_exp_cfg(config: str) -> dict:
    return _load_yaml(config)


def _write_yaml(path: str | Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def _artifact_prefix(exp_cfg: dict) -> str:
    prefix = str(exp_cfg.get("artifact_prefix", "")).strip()
    if prefix:
        return prefix
    return str(exp_cfg.get("experiment_name", "experiment")).strip()


def _read_json_file(path: str | Path) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = [header, sep]
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if pd.isna(val):
                vals.append("")
            elif isinstance(val, float):
                vals.append(f"{val:.6f}")
            else:
                vals.append(str(val))
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join(rows)


def _resolve_model(
    model_name: str,
    model_cfg: dict,
    task: str = "regression",
    *,
    exp_cfg: Optional[dict] = None,
    variant_name: Optional[str] = None,
):
    """Return (ModelClass, config_dict) for a given model name."""
    m = model_name.lower().strip()

    def _task_cfg(name: str) -> dict:
        cfg = model_cfg.get(name, {})
        if isinstance(cfg, dict) and task in cfg and isinstance(cfg[task], dict):
            base_cfg = copy.deepcopy(cfg[task])
        else:
            base_cfg = copy.deepcopy(cfg if isinstance(cfg, dict) else {})
        if exp_cfg and variant_name:
            tuned_cfg = (
                exp_cfg.get("tuning", {})
                .get("best_params", {})
                .get(name, {})
                .get(task, {})
                .get(variant_name, {})
            )
            if isinstance(tuned_cfg, dict) and tuned_cfg:
                base_cfg.update(copy.deepcopy(tuned_cfg))
        return base_cfg

    if m == "ridge":
        from src.models.ridge import RidgeModel
        cfg = _task_cfg("ridge")
        cfg["task"] = task
        return RidgeModel, cfg
    elif m == "lasso":
        from src.models.lasso import LassoModel
        cfg = _task_cfg("lasso")
        cfg["task"] = task
        return LassoModel, cfg
    elif m in ("lgbm", "gbm"):
        from src.models.lgbm import GBMModel
        cfg = _task_cfg("lgbm")
        cfg["task"] = task
        return GBMModel, cfg
    elif m in ("xgboost", "xgb"):
        from src.models.xgb import XGBoostModel
        cfg = _task_cfg("xgboost")
        if not cfg:
            cfg = _task_cfg("lgbm")
        cfg["task"] = task
        return XGBoostModel, cfg
    elif m == "lstm":
        from src.models.lstm import LSTMModel
        cfg = _task_cfg("lstm")
        if not cfg:
            cfg = model_cfg.get("deep_learning", {}) if isinstance(model_cfg.get("deep_learning", {}), dict) else {}
        cfg["task"] = task
        return LSTMModel, cfg
    elif m in ("cnn_lstm", "cnnlstm"):
        from src.models.cnn_lstm import CNNLSTMModel
        cfg = _task_cfg("cnn_lstm")
        if not cfg:
            cfg = model_cfg.get("deep_learning", {}) if isinstance(model_cfg.get("deep_learning", {}), dict) else {}
        cfg["task"] = task
        return CNNLSTMModel, cfg
    elif m == "gru":
        from src.models.gru import GRUModel
        cfg = _task_cfg("gru")
        if not cfg:
            cfg = model_cfg.get("deep_learning", {}) if isinstance(model_cfg.get("deep_learning", {}), dict) else {}
        cfg["task"] = task
        return GRUModel, cfg
    elif m == "tcn":
        from src.models.tcn import TCNModel
        cfg = _task_cfg("tcn")
        if not cfg:
            cfg = model_cfg.get("deep_learning", {}) if isinstance(model_cfg.get("deep_learning", {}), dict) else {}
        cfg["task"] = task
        return TCNModel, cfg
    elif m == "svm":
        from src.models.svm import SVMModel
        cfg = _task_cfg("svm")
        cfg["task"] = task
        return SVMModel, cfg
    elif m in ("rf", "random_forest"):
        from src.models.rf import RFModel
        cfg = _task_cfg("rf")
        cfg["task"] = task
        return RFModel, cfg
    else:
        raise ValueError(
            f"Unknown or unimplemented model: {model_name}. "
            "Implemented now: ridge, lasso, lgbm, xgboost, svm, rf, lstm, cnn_lstm, gru, tcn."
        )


def _resolve_selected_model(model_name: Optional[str], exp_cfg: dict) -> str:
    """
    Resolve model from CLI first, then config.
    Forces explicit decision by user/config and avoids silent defaults.
    """
    if model_name:
        return model_name.strip().lower()
    selected = (
        exp_cfg.get("decision", {})
        .get("selected_model")
    )
    if isinstance(selected, str) and selected.strip():
        return selected.strip().lower()
    raise click.ClickException(
        "Model is not selected. Pass --model explicitly or set "
        "decision.selected_model in configs/experiment.yaml."
    )


def _run_walk_forward_compat(run_walk_forward_fn, **kwargs):
    """Call run_walk_forward with backward-compatible kwargs."""
    if "horizon" not in inspect.signature(run_walk_forward_fn).parameters:
        kwargs.pop("horizon", None)
    return run_walk_forward_fn(**kwargs)


def _resolve_task(task: Optional[str], exp_cfg: dict, data_cfg: dict) -> str:
    if task in ("regression", "classification"):
        return task
    tasks_cfg = exp_cfg.get("tasks", {})
    if tasks_cfg.get("regression", {}).get("enabled", False):
        return "regression"
    if tasks_cfg.get("classification", {}).get("enabled", False):
        return "classification"
    # Safe fallback aligned with current pipeline behavior.
    _ = data_cfg
    return "regression"


def _resolve_dataset_variant(dataset_variant: Optional[str], exp_cfg: dict) -> str:
    if dataset_variant:
        return dataset_variant
    configured = exp_cfg.get("datasets", {}).get("variants", [])
    if "all" in configured:
        return "all"
    return configured[0] if configured else "all"


def _resolve_label_col(task: str, exp_cfg: dict, data_cfg: dict) -> str:
    if task == "classification":
        return (
            exp_cfg.get("tasks", {})
            .get("classification", {})
            .get(
                "label_col",
                data_cfg.get("prediction", {}).get("classification_target_col", "direction_h"),
            )
        )
    return (
        exp_cfg.get("tasks", {})
        .get("regression", {})
        .get("label_col", data_cfg.get("prediction", {}).get("target_col", "log_ret_h"))
    )


def _glassnode_cfg(data_cfg: dict) -> dict:
    onchain_cfg = data_cfg.get("onchain", {})
    providers = onchain_cfg.get("providers", {})
    gn_cfg = providers.get("glassnode", {})
    return {
        "use_glassnode": bool(gn_cfg.get("enabled", False)),
        "glassnode_metrics": gn_cfg.get("metrics", []) or [],
        "glassnode_cache_dir": gn_cfg.get("cache_dir", "data/raw/glassnode"),
        "glassnode_api_key_env": gn_cfg.get("api_key_env", "GLASSNODE_API_KEY"),
        "glassnode_asset": gn_cfg.get("asset", "BTC"),
        "glassnode_interval": gn_cfg.get("interval", "24h"),
    }


def _onchain_cfg(data_cfg: dict) -> dict:
    onchain_cfg = data_cfg.get("onchain", {})
    providers = onchain_cfg.get("providers", {})
    primary = str(onchain_cfg.get("primary_provider", "blockchain")).strip().lower()

    blockchain_cfg = providers.get("blockchain", {})
    coinmetrics_cfg = providers.get("coinmetrics", {})

    if primary == "coinmetrics":
        metrics = coinmetrics_cfg.get("metrics", []) or []
        cache_dir = coinmetrics_cfg.get("cache_dir", "data/raw/coinmetrics")
    else:
        metrics = onchain_cfg.get("metrics", []) or []
        cache_dir = blockchain_cfg.get("cache_dir", onchain_cfg.get("cache_dir", "data/raw/blockchain"))

    return {
        "onchain_provider": primary,
        "onchain_metrics": metrics,
        "onchain_timespan": blockchain_cfg.get("timespan", onchain_cfg.get("timespan", "all")),
        "onchain_cache_dir": blockchain_cfg.get("cache_dir", onchain_cfg.get("cache_dir", "data/raw/blockchain")),
        "coinmetrics_cache_dir": coinmetrics_cfg.get("cache_dir", "data/raw/coinmetrics"),
        "coinmetrics_asset": coinmetrics_cfg.get("asset", "btc"),
        "coinmetrics_frequency": coinmetrics_cfg.get("frequency", "1d"),
        "coinmetrics_start_time": coinmetrics_cfg.get("start_time"),
        "coinmetrics_end_time": coinmetrics_cfg.get("end_time"),
        "resolved_metrics": metrics,
        "resolved_cache_dir": cache_dir,
    }


def _build_dataset_kwargs(
    exp_cfg: dict,
    data_cfg: dict,
    force: bool = False,
    output_path: Optional[str] = None,
    drop_label_na: bool = True,
) -> dict:
    feat_cfg = exp_cfg.get("features", {})
    pred_cfg = data_cfg.get("prediction", {})
    onchain_cfg = _onchain_cfg(data_cfg)
    return {
        "symbol": exp_cfg.get("symbol", "BTC-USD"),
        "start_date": data_cfg["price"]["start_date"],
        "end_date": data_cfg["price"].get("end_date"),
        "horizon": int(pred_cfg.get("horizon", 1)),
        "label_horizon_days": int(exp_cfg.get("label_horizon_days", pred_cfg.get("horizon", 1))),
        "use_price": feat_cfg.get("price_factors", True),
        "use_onchain": feat_cfg.get("onchain_factors", False),
        "use_macro": feat_cfg.get("macro_factors", False),
        "price_cache_dir": data_cfg["price"]["cache_dir"],
        "onchain_provider": onchain_cfg["onchain_provider"],
        "onchain_metrics": onchain_cfg["onchain_metrics"],
        "onchain_timespan": onchain_cfg["onchain_timespan"],
        "onchain_cache_dir": onchain_cfg["onchain_cache_dir"],
        "coinmetrics_cache_dir": onchain_cfg["coinmetrics_cache_dir"],
        "coinmetrics_asset": onchain_cfg["coinmetrics_asset"],
        "coinmetrics_frequency": onchain_cfg["coinmetrics_frequency"],
        "coinmetrics_start_time": onchain_cfg["coinmetrics_start_time"],
        "coinmetrics_end_time": onchain_cfg["coinmetrics_end_time"],
        **_glassnode_cfg(data_cfg),
        "macro_cache_dir": data_cfg.get("macro", {}).get("cache_dir", "data/raw/macro"),
        "macro_use_dummy": data_cfg.get("macro", {}).get("use_dummy", True),
        "macro_lag_days": data_cfg.get("macro", {}).get("release_lag_days", 1),
        "force_download": force,
        "output_path": output_path,
        "drop_label_na": drop_label_na,
    }


def _load_or_build_feature_dataset(
    exp_cfg: dict,
    data_cfg: dict,
    *,
    force: bool = False,
    keep_unlabeled_tail: bool = False,
) -> pd.DataFrame:
    prefix = _artifact_prefix(exp_cfg)
    feat_path = f"data/features/{prefix}.parquet"

    if Path(feat_path).exists() and not keep_unlabeled_tail and not force:
        df = pd.read_parquet(feat_path)
        logger.info(f"Loaded features from {feat_path} ({df.shape})")
        return df

    from src.datasets.build_dataset import build_dataset

    if Path(feat_path).exists() and keep_unlabeled_tail and not force:
        logger.info("Rebuilding feature dataset to retain latest unlabeled row for prediction.")
    elif not Path(feat_path).exists():
        logger.info("Feature file not found, building dataset …")

    return build_dataset(
        **_build_dataset_kwargs(
            exp_cfg,
            data_cfg,
            force=force,
            output_path=None if keep_unlabeled_tail else feat_path,
            drop_label_na=not keep_unlabeled_tail,
        )
    )


def _resolve_feature_cols_for_variant(
    df: pd.DataFrame,
    task_name: str,
    variant_name: str,
    exp_cfg: dict,
    data_cfg: dict,
) -> tuple[str, list[str]]:
    from src.datasets.build_dataset import get_feature_cols_by_variant

    label_col = _resolve_label_col(task_name, exp_cfg, data_cfg)
    feature_cols = get_feature_cols_by_variant(
        df,
        label_col=label_col,
        dataset_variant=variant_name,
    )
    if variant_name.startswith("boruta_"):
        labeled_df = df.dropna(subset=[label_col]).copy()
        feature_cols = _apply_boruta_lasso_feature_selection(
            df=labeled_df,
            feature_cols=feature_cols,
            label_col=label_col,
            task=task_name,
            exp_cfg=exp_cfg,
            data_cfg=data_cfg,
        )
    if not feature_cols:
        raise RuntimeError(
            f"No features resolved for dataset_variant={variant_name}. "
            "Check feature-engineering columns and config."
        )
    return label_col, feature_cols


def _model_artifact_paths(
    exp_cfg: dict,
    model_name: str,
    task_name: str,
    variant_name: str,
) -> tuple[Path, Path]:
    model_dir = Path(exp_cfg.get("output", {}).get("model_dir", "models_saved"))
    model_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{_artifact_prefix(exp_cfg)}_{model_name}_{task_name}_{variant_name}"
    return model_dir / f"{stem}.pkl", model_dir / f"{stem}_meta.json"


def _split_final_fit_data(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    val_months: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    labeled = df.dropna(subset=feature_cols + [label_col]).copy()
    if len(labeled) < 50:
        raise RuntimeError(
            f"Too few labeled rows ({len(labeled)}) for final model fit."
        )
    val_days = max(20, int(round(val_months * 30)))
    if len(labeled) > val_days + 50:
        return labeled.iloc[:-val_days].copy(), labeled.iloc[-val_days:].copy()
    return labeled.copy(), pd.DataFrame(columns=labeled.columns)


def _fit_final_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    model_cls,
    model_config: dict,
    val_months: float,
):
    train_df, val_df = _split_final_fit_data(
        df=df,
        feature_cols=feature_cols,
        label_col=label_col,
        val_months=val_months,
    )
    model = model_cls(config=model_config)
    model.fit(
        train_df[feature_cols],
        train_df[label_col].values,
        val_df[feature_cols] if len(val_df) else None,
        val_df[label_col].values if len(val_df) else None,
    )
    return model, train_df, val_df


def _prepare_model_for_history_scoring(model) -> None:
    """
    Reset sequence-history cache when a final DL model is reused to score
    the full timeline from the beginning.

    Saved DL artifacts keep the tail of the train/validation window so they
    can score the next unseen sample. That cache is wrong for full-history
    in-sample scoring because it would prepend the END of the train window
    to the START of the full dataset.
    """
    if hasattr(model, "_history_tail"):
        model._history_tail = None


def _fixed_halving_periods(end_date: pd.Timestamp | str) -> list[tuple[str, pd.Timestamp, pd.Timestamp]]:
    end_ts = pd.Timestamp(end_date)
    if end_ts.tzinfo is None:
        end_ts = end_ts.tz_localize("UTC")
    else:
        end_ts = end_ts.tz_convert("UTC")
    return [
        ("full_sample", pd.Timestamp.min.tz_localize("UTC"), end_ts),
        ("cycle_2016_2020", pd.Timestamp("2016-07-09", tz="UTC"), pd.Timestamp("2020-05-10", tz="UTC")),
        ("cycle_2020_2024", pd.Timestamp("2020-05-11", tz="UTC"), pd.Timestamp("2024-04-19", tz="UTC")),
        ("cycle_2024_end", pd.Timestamp("2024-04-20", tz="UTC"), end_ts),
    ]


def _fixed_strategy_specs() -> list[dict[str, object]]:
    specs: list[dict[str, object]] = [{"name": "long_only_sign", "kind": "long_only_sign"}]
    for band in (0.0025, 0.005, 0.01):
        specs.append({"name": f"long_only_band_{band:g}", "kind": "long_only_band", "band": band})
    specs.append({"name": "full_exposure_sign", "kind": "full_exposure_sign"})
    for band in (0.0025, 0.005, 0.01):
        specs.append({"name": f"sign_band_{band:g}", "kind": "sign_band", "band": band})
    for q in (0.05, 0.10, 0.20):
        specs.append({"name": f"quantile_long_only_{q:.2f}", "kind": "quantile_long_only", "q": q})
    for q in (0.05, 0.10, 0.20):
        specs.append({"name": f"quantile_ls_{q:.2f}", "kind": "quantile_ls", "q": q})
    return specs


def _signal_from_strategy_spec(scores: pd.Series, spec: dict[str, object]) -> pd.Series:
    kind = str(spec["kind"])
    signal = pd.Series(0.0, index=scores.index, dtype=float)
    if kind == "long_only_sign":
        signal.loc[scores >= 0.0] = 1.0
        return signal
    if kind == "long_only_band":
        band = float(spec["band"])
        signal.loc[scores >= band] = 1.0
        return signal
    if kind == "full_exposure_sign":
        signal.loc[scores >= 0.0] = 1.0
        signal.loc[scores < 0.0] = -1.0
        return signal
    if kind == "sign_band":
        band = float(spec["band"])
        signal.loc[scores >= band] = 1.0
        signal.loc[scores <= -band] = -1.0
        return signal
    if kind == "quantile_long_only":
        q = float(spec["q"])
        threshold = float(scores.quantile(1.0 - q))
        signal.loc[scores >= threshold] = 1.0
        return signal
    if kind == "quantile_ls":
        q = float(spec["q"])
        upper = float(scores.quantile(1.0 - q))
        lower = float(scores.quantile(q))
        signal.loc[scores >= upper] = 1.0
        signal.loc[scores <= lower] = -1.0
        return signal
    raise ValueError(f"Unknown strategy kind: {kind}")


def _tuning_root(exp_cfg: dict) -> Path:
    root = Path(exp_cfg.get("output", {}).get("summary_dir", "reports/summary")) / "tuning"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_best_params_to_config(
    config_path: str | Path,
    exp_cfg: dict,
    *,
    model_name: str,
    task_name: str,
    variant_name: str,
    params: dict,
    objective: str,
    objective_value: float,
) -> None:
    exp_cfg.setdefault("tuning", {})
    tuning_cfg = exp_cfg["tuning"]
    tuning_cfg.setdefault("best_params", {})
    tuning_cfg["best_params"].setdefault(model_name, {})
    tuning_cfg["best_params"][model_name].setdefault(task_name, {})
    tuning_cfg["best_params"][model_name][task_name][variant_name] = copy.deepcopy(params)

    tuning_cfg.setdefault("best_results", {})
    tuning_cfg["best_results"].setdefault(model_name, {})
    tuning_cfg["best_results"][model_name].setdefault(task_name, {})
    tuning_cfg["best_results"][model_name][task_name][variant_name] = {
        "objective": objective,
        "objective_value": float(objective_value),
        "updated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    }
    _write_yaml(config_path, exp_cfg)


def _run_followup_cli_step(args: list[str], step_name: str) -> None:
    click.echo(f"\n── {step_name} ──")
    click.echo("  " + " ".join(args))
    result = subprocess.run(args, check=False)
    if result.returncode != 0:
        raise click.ClickException(f"{step_name} failed with exit code {result.returncode}.")


def _default_tuning_metric(task_name: str, exp_cfg: dict) -> str:
    primary = exp_cfg.get("evaluation", {}).get("primary_selection_metric", {})
    if task_name == "classification":
        return str(primary.get("classification", "f1"))
    return str(primary.get("regression", "rmse"))


def _metric_direction(metric_name: str) -> str:
    maximize = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "ic",
        "rank_ic",
        "r2",
        "oos_r2",
        "directional_accuracy",
    }
    return "max" if metric_name.lower() in maximize else "min"


def _score_metric(metric_name: str, metric_value: float) -> float:
    if pd.isna(metric_value):
        return float("-inf")
    return float(metric_value) if _metric_direction(metric_name) == "max" else float(-metric_value)


def _builtin_tuning_space(model_name: str, task_name: str) -> dict[str, object]:
    model_key = model_name.lower().strip()
    task_key = task_name.lower().strip()
    spaces: dict[tuple[str, str], dict[str, object]] = {
        ("rf", "classification"): {
            "n_estimators": [300, 500, 800, 1200],
            "max_depth": [4, 6, 8, 12, 16, None],
            "min_samples_split": [2, 4, 8, 16],
            "min_samples_leaf": [1, 2, 4, 8],
            "max_features": ["sqrt", "log2", 0.5, 0.8],
            "class_weight": ["balanced", "balanced_subsample", None],
        },
        ("rf", "regression"): {
            "n_estimators": [300, 500, 800, 1200],
            "max_depth": [4, 6, 8, 12, 16, None],
            "min_samples_split": [2, 4, 8, 16],
            "min_samples_leaf": [1, 2, 4, 8],
            "max_features": ["sqrt", "log2", 0.5, 0.8],
        },
        ("svm", "classification"): {
            "C": {"distribution": "loguniform", "low": 0.1, "high": 100.0},
            "gamma": ["scale", "auto", 0.001, 0.01, 0.1],
            "class_weight": ["balanced", None],
        },
        ("svm", "regression"): {
            "C": {"distribution": "loguniform", "low": 0.1, "high": 100.0},
            "gamma": ["scale", "auto", 0.001, 0.01, 0.1],
            "epsilon": {"distribution": "loguniform", "low": 0.001, "high": 0.1},
        },
        ("lgbm", "classification"): {
            "n_estimators": [300, 500, 800, 1200],
            "learning_rate": {"distribution": "loguniform", "low": 0.01, "high": 0.2},
            "max_depth": [3, 4, 5, 6, 8],
            "num_leaves": [15, 31, 63, 127],
            "min_child_samples": [10, 20, 30, 50],
            "subsample": {"distribution": "uniform", "low": 0.6, "high": 1.0},
            "colsample_bytree": {"distribution": "uniform", "low": 0.6, "high": 1.0},
            "reg_alpha": {"distribution": "loguniform", "low": 0.001, "high": 1.0},
            "reg_lambda": {"distribution": "loguniform", "low": 0.1, "high": 10.0},
        },
        ("lgbm", "regression"): {
            "n_estimators": [300, 500, 800, 1200],
            "learning_rate": {"distribution": "loguniform", "low": 0.01, "high": 0.2},
            "max_depth": [3, 4, 5, 6, 8],
            "num_leaves": [15, 31, 63, 127],
            "min_child_samples": [10, 20, 30, 50],
            "subsample": {"distribution": "uniform", "low": 0.6, "high": 1.0},
            "colsample_bytree": {"distribution": "uniform", "low": 0.6, "high": 1.0},
            "reg_alpha": {"distribution": "loguniform", "low": 0.001, "high": 1.0},
            "reg_lambda": {"distribution": "loguniform", "low": 0.1, "high": 10.0},
        },
        ("xgboost", "classification"): {
            "n_estimators": [300, 500, 800, 1200],
            "learning_rate": {"distribution": "loguniform", "low": 0.01, "high": 0.2},
            "max_depth": [3, 4, 5, 6, 8],
            "subsample": {"distribution": "uniform", "low": 0.6, "high": 1.0},
            "colsample_bytree": {"distribution": "uniform", "low": 0.6, "high": 1.0},
            "reg_alpha": {"distribution": "loguniform", "low": 0.001, "high": 1.0},
            "reg_lambda": {"distribution": "loguniform", "low": 0.1, "high": 10.0},
        },
        ("xgboost", "regression"): {
            "n_estimators": [300, 500, 800, 1200],
            "learning_rate": {"distribution": "loguniform", "low": 0.01, "high": 0.2},
            "max_depth": [3, 4, 5, 6, 8],
            "subsample": {"distribution": "uniform", "low": 0.6, "high": 1.0},
            "colsample_bytree": {"distribution": "uniform", "low": 0.6, "high": 1.0},
            "reg_alpha": {"distribution": "loguniform", "low": 0.001, "high": 1.0},
            "reg_lambda": {"distribution": "loguniform", "low": 0.1, "high": 10.0},
        },
        ("lstm", "classification"): {
            "timesteps": [5, 10, 15, 20],
            "hidden_dim": [32, 64, 96, 128],
            "num_layers": [1, 2, 3],
            "dropout": {"distribution": "uniform", "low": 0.0, "high": 0.4},
            "batch_size": [32, 64, 128],
            "max_epochs": [30, 40, 60, 80],
            "early_stopping_patience": [5, 8, 10, 12],
            "learning_rate": {"distribution": "loguniform", "low": 1e-4, "high": 5e-3},
            "weight_decay": {"distribution": "loguniform", "low": 1e-6, "high": 1e-2},
        },
        ("lstm", "regression"): {
            "timesteps": [5, 10, 15, 20],
            "hidden_dim": [32, 64, 96, 128],
            "num_layers": [1, 2, 3],
            "dropout": {"distribution": "uniform", "low": 0.0, "high": 0.4},
            "batch_size": [32, 64, 128],
            "max_epochs": [30, 40, 60, 80],
            "early_stopping_patience": [5, 8, 10, 12],
            "learning_rate": {"distribution": "loguniform", "low": 1e-4, "high": 5e-3},
            "weight_decay": {"distribution": "loguniform", "low": 1e-6, "high": 1e-2},
        },
        ("cnn_lstm", "classification"): {
            "timesteps": [5, 10, 15, 20],
            "conv_channels": [16, 32, 64],
            "kernel_size": [2, 3, 5],
            "hidden_dim": [32, 64, 96, 128],
            "num_layers": [1, 2],
            "dropout": {"distribution": "uniform", "low": 0.0, "high": 0.4},
            "batch_size": [32, 64, 128],
            "max_epochs": [30, 40, 60, 80],
            "early_stopping_patience": [5, 8, 10, 12],
            "learning_rate": {"distribution": "loguniform", "low": 1e-4, "high": 5e-3},
            "weight_decay": {"distribution": "loguniform", "low": 1e-6, "high": 1e-2},
        },
        ("cnn_lstm", "regression"): {
            "timesteps": [5, 10, 15, 20],
            "conv_channels": [16, 32, 64],
            "kernel_size": [2, 3, 5],
            "hidden_dim": [32, 64, 96, 128],
            "num_layers": [1, 2],
            "dropout": {"distribution": "uniform", "low": 0.0, "high": 0.4},
            "batch_size": [32, 64, 128],
            "max_epochs": [30, 40, 60, 80],
            "early_stopping_patience": [5, 8, 10, 12],
            "learning_rate": {"distribution": "loguniform", "low": 1e-4, "high": 5e-3},
            "weight_decay": {"distribution": "loguniform", "low": 1e-6, "high": 1e-2},
        },
        ("gru", "classification"): {
            "timesteps": [5, 10, 15, 20],
            "hidden_dim": [32, 64, 96, 128],
            "num_layers": [1, 2, 3],
            "dropout": {"distribution": "uniform", "low": 0.0, "high": 0.4},
            "batch_size": [32, 64, 128],
            "max_epochs": [30, 40, 60, 80],
            "early_stopping_patience": [5, 8, 10, 12],
            "learning_rate": {"distribution": "loguniform", "low": 1e-4, "high": 5e-3},
            "weight_decay": {"distribution": "loguniform", "low": 1e-6, "high": 1e-2},
        },
        ("gru", "regression"): {
            "timesteps": [5, 10, 15, 20],
            "hidden_dim": [32, 64, 96, 128],
            "num_layers": [1, 2, 3],
            "dropout": {"distribution": "uniform", "low": 0.0, "high": 0.4},
            "batch_size": [32, 64, 128],
            "max_epochs": [30, 40, 60, 80],
            "early_stopping_patience": [5, 8, 10, 12],
            "learning_rate": {"distribution": "loguniform", "low": 1e-4, "high": 5e-3},
            "weight_decay": {"distribution": "loguniform", "low": 1e-6, "high": 1e-2},
        },
        ("tcn", "classification"): {
            "timesteps": [8, 12, 16, 20],
            "channels": [[16, 16, 16], [32, 32, 32], [32, 64, 64], [64, 64, 64]],
            "kernel_size": [2, 3, 5],
            "dropout": {"distribution": "uniform", "low": 0.0, "high": 0.4},
            "batch_size": [32, 64, 128],
            "max_epochs": [30, 40, 60, 80],
            "early_stopping_patience": [5, 8, 10, 12],
            "learning_rate": {"distribution": "loguniform", "low": 1e-4, "high": 5e-3},
            "weight_decay": {"distribution": "loguniform", "low": 1e-6, "high": 1e-2},
        },
        ("tcn", "regression"): {
            "timesteps": [8, 12, 16, 20],
            "channels": [[16, 16, 16], [32, 32, 32], [32, 64, 64], [64, 64, 64]],
            "kernel_size": [2, 3, 5],
            "dropout": {"distribution": "uniform", "low": 0.0, "high": 0.4},
            "batch_size": [32, 64, 128],
            "max_epochs": [30, 40, 60, 80],
            "early_stopping_patience": [5, 8, 10, 12],
            "learning_rate": {"distribution": "loguniform", "low": 1e-4, "high": 5e-3},
            "weight_decay": {"distribution": "loguniform", "low": 1e-6, "high": 1e-2},
        },
    }
    return copy.deepcopy(spaces.get((model_key, task_key), {}))


def _resolve_tuning_space(exp_cfg: dict, model_name: str, task_name: str) -> dict[str, object]:
    tuning_cfg = exp_cfg.get("tuning", {})
    search_spaces = tuning_cfg.get("search_spaces", {})
    model_spaces = search_spaces.get(model_name, {}) if isinstance(search_spaces, dict) else {}
    task_space = model_spaces.get(task_name, {}) if isinstance(model_spaces, dict) else {}
    if isinstance(task_space, dict) and task_space:
        return copy.deepcopy(task_space)
    return _builtin_tuning_space(model_name, task_name)


def _search_value_to_text(spec) -> str:
    if isinstance(spec, list):
        return ", ".join(str(x) for x in spec)
    if isinstance(spec, dict):
        dist = str(spec.get("distribution", "categorical")).lower()
        if dist == "categorical":
            choices = spec.get("choices", [])
            return f"categorical({', '.join(str(x) for x in choices)})"
        if dist in {"uniform", "loguniform", "int"}:
            low = spec.get("low")
            high = spec.get("high")
            step = spec.get("step")
            if step is not None:
                return f"{dist}[{low}, {high}] step={step}"
            return f"{dist}[{low}, {high}]"
    return str(spec)


def _collect_search_space_rows(exp_cfg: dict, model_name: Optional[str], task_name: Optional[str]) -> list[dict[str, str]]:
    comparison_cfg = exp_cfg.get("comparison", {})
    ml_models = [str(m).lower() for m in comparison_cfg.get("ml_models", [])]
    dl_models = [str(m).lower() for m in comparison_cfg.get("dl_models", [])]
    configured_models = list(dict.fromkeys(ml_models + dl_models + ["ridge", "lasso", "svm", "rf", "lgbm", "xgboost"]))
    tasks = [task_name] if task_name else ["classification", "regression"]
    models = [model_name.lower()] if model_name else configured_models

    rows: list[dict[str, str]] = []
    for model in models:
        for task in tasks:
            space = _resolve_tuning_space(exp_cfg, model, task)
            if not space:
                continue
            for param_name, spec in space.items():
                rows.append(
                    {
                        "model": model,
                        "task": task,
                        "parameter": str(param_name),
                        "candidate_space": _search_value_to_text(spec),
                    }
                )
    return rows


def _sample_search_value(spec, rng: random.Random):
    if isinstance(spec, list):
        return copy.deepcopy(rng.choice(spec))
    if isinstance(spec, dict):
        dist = str(spec.get("distribution", "categorical")).lower()
        if dist == "categorical":
            choices = spec.get("choices", [])
            if not choices:
                raise ValueError("categorical search space requires non-empty choices")
            return copy.deepcopy(rng.choice(list(choices)))
        low = spec.get("low")
        high = spec.get("high")
        if low is None or high is None:
            raise ValueError(f"distribution '{dist}' requires low/high bounds")
        if dist == "uniform":
            return float(rng.uniform(float(low), float(high)))
        if dist == "loguniform":
            lo = np.log(float(low))
            hi = np.log(float(high))
            return float(np.exp(rng.uniform(lo, hi)))
        if dist == "int":
            step = int(spec.get("step", 1))
            values = list(range(int(low), int(high) + 1, step))
            return int(rng.choice(values))
    return copy.deepcopy(spec)


def _sample_param_config(
    base_config: dict,
    search_space: dict[str, object],
    rng: random.Random,
    trial_index: int,
) -> dict:
    sampled = copy.deepcopy(base_config)
    for key, spec in search_space.items():
        sampled[key] = _sample_search_value(spec, rng)
    sampled["random_state"] = int(sampled.get("random_state", 42)) + int(trial_index)
    return sampled


def _evaluate_model_config(
    model_cls,
    model_config: dict,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    task_name: str,
    metric_prefix_name: str,
) -> tuple[dict[str, float], np.ndarray]:
    from src.evaluation.metrics import compute_classification_metrics, compute_metrics, rank_ic

    model = model_cls(config=model_config)
    model.fit(
        train_df[feature_cols],
        train_df[label_col].values,
        val_df[feature_cols] if len(val_df) else None,
        val_df[label_col].values if len(val_df) else None,
    )
    y_pred = model.predict(val_df[feature_cols])
    if task_name == "classification":
        metrics = compute_classification_metrics(
            val_df[label_col].values,
            y_pred,
            prefix=f"{metric_prefix_name}_{task_name}_val",
            threshold=0.5,
        )
    else:
        metrics = compute_metrics(
            val_df[label_col].values,
            y_pred,
            prefix=f"{metric_prefix_name}_{task_name}_val",
        )
        metrics[f"{metric_prefix_name}_{task_name}_val_rank_ic"] = rank_ic(
            val_df[label_col].values,
            y_pred,
        )
    return metrics, y_pred


def _apply_boruta_proxy_selection(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    task: str,
    exp_cfg: dict,
    data_cfg: dict,
) -> list[str]:
    """
    Lightweight Boruta-like proxy feature filtering.
    Uses train-only chronological subset and RF importances.
    """
    if len(feature_cols) <= 1:
        return feature_cols
    split_cfg = data_cfg.get("split", {})
    train_ratio = float(split_cfg.get("train_ratio", 0.8))
    cut = max(1, int(len(df) * train_ratio))
    train_df = df.iloc[:cut].dropna(subset=feature_cols + [label_col])
    if len(train_df) < 50:
        logger.warning("[feature_select] Too few rows for Boruta proxy; skipping.")
        return feature_cols

    boruta_cfg = exp_cfg.get("datasets", {}).get("boruta", {})
    n_estimators = int(boruta_cfg.get("n_estimators", 300))
    rs = int(boruta_cfg.get("random_state", 42))

    X = train_df[feature_cols]
    y = train_df[label_col].values

    try:
        if task == "classification":
            from sklearn.ensemble import RandomForestClassifier
            rf = RandomForestClassifier(
                n_estimators=n_estimators,
                random_state=rs,
                n_jobs=-1,
            )
        else:
            from sklearn.ensemble import RandomForestRegressor
            rf = RandomForestRegressor(
                n_estimators=n_estimators,
                random_state=rs,
                n_jobs=-1,
            )
        rf.fit(X, y)
        importances = np.asarray(rf.feature_importances_, dtype=float)
        threshold = float(np.nanmedian(importances))
        selected = [c for c, imp in zip(feature_cols, importances) if float(imp) >= threshold]
        if not selected:
            selected = feature_cols
        logger.info(
            f"[feature_select] Boruta proxy kept {len(selected)}/{len(feature_cols)} features."
        )
        return selected
    except Exception as exc:
        logger.warning(f"[feature_select] Boruta proxy failed ({exc}); using all features.")
        return feature_cols


def _apply_lasso_refinement_selection(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    task: str,
    exp_cfg: dict,
    data_cfg: dict,
) -> list[str]:
    """
    Lasso/L1 refinement on top of Boruta-selected features.
    - regression: Lasso
    - classification: LogisticRegression(L1)
    """
    if len(feature_cols) <= 1:
        return feature_cols
    split_cfg = data_cfg.get("split", {})
    train_ratio = float(split_cfg.get("train_ratio", 0.8))
    cut = max(1, int(len(df) * train_ratio))
    train_df = df.iloc[:cut].dropna(subset=feature_cols + [label_col])
    if len(train_df) < 80:
        logger.warning("[feature_select] Too few rows for Lasso refinement; skipping.")
        return feature_cols

    fs_cfg = exp_cfg.get("datasets", {}).get("feature_selection", {})
    lasso_cfg = fs_cfg.get("lasso", {})
    coef_eps = float(lasso_cfg.get("coef_threshold", 1e-8))
    rs = int(lasso_cfg.get("random_state", 42))

    X = train_df[feature_cols]
    y = train_df[label_col].values

    try:
        if task == "classification":
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler

            clf = LogisticRegression(
                penalty="l1",
                solver=str(lasso_cfg.get("solver", "liblinear")),
                C=float(lasso_cfg.get("C", 0.5)),
                class_weight=lasso_cfg.get("class_weight", "balanced"),
                max_iter=int(lasso_cfg.get("max_iter", 2000)),
                random_state=rs,
            )
            pipe = Pipeline([("scaler", StandardScaler()), ("l1", clf)])
            pipe.fit(X, y)
            coefs = np.abs(pipe.named_steps["l1"].coef_).ravel()
        else:
            from sklearn.linear_model import Lasso
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler

            reg = Lasso(
                alpha=float(lasso_cfg.get("alpha", 0.001)),
                max_iter=int(lasso_cfg.get("max_iter", 5000)),
                tol=float(lasso_cfg.get("tol", 1e-4)),
                random_state=rs,
            )
            pipe = Pipeline([("scaler", StandardScaler()), ("l1", reg)])
            pipe.fit(X, y)
            coefs = np.abs(pipe.named_steps["l1"].coef_).ravel()

        selected = [c for c, coef in zip(feature_cols, coefs) if float(coef) > coef_eps]
        if not selected:
            # Keep strongest few if all coefficients shrink to zero.
            topk = max(1, min(10, len(feature_cols)))
            order = np.argsort(-coefs)[:topk]
            selected = [feature_cols[i] for i in order]
        logger.info(
            f"[feature_select] Lasso refinement kept {len(selected)}/{len(feature_cols)} features."
        )
        return selected
    except Exception as exc:
        logger.warning(f"[feature_select] Lasso refinement failed ({exc}); keeping Boruta set.")
        return feature_cols


def _apply_boruta_lasso_feature_selection(
    df: pd.DataFrame,
    feature_cols: list[str],
    label_col: str,
    task: str,
    exp_cfg: dict,
    data_cfg: dict,
) -> list[str]:
    """
    Two-stage feature extraction:
      1) Boruta proxy (RF importance filter)
      2) Lasso/L1 refinement
    """
    fs_cfg = exp_cfg.get("datasets", {}).get("feature_selection", {})
    method = str(fs_cfg.get("method", "boruta_lasso")).lower()

    boruta_selected = _apply_boruta_proxy_selection(
        df=df,
        feature_cols=feature_cols,
        label_col=label_col,
        task=task,
        exp_cfg=exp_cfg,
        data_cfg=data_cfg,
    )
    if method in ("boruta_lasso", "lasso_boruta", "boruta+lasso"):
        return _apply_lasso_refinement_selection(
            df=df,
            feature_cols=boruta_selected,
            label_col=label_col,
            task=task,
            exp_cfg=exp_cfg,
            data_cfg=data_cfg,
        )
    return boruta_selected


# ── CLI group ─────────────────────────────────────────────────

@click.group()
def cli():
    """Crypto price prediction & backtesting pipeline."""
    pass


# ── download-data ─────────────────────────────────────────────

@cli.command("download-data")
@click.option("--config", default="configs/experiment.yaml",
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
    onchain_cfg = _onchain_cfg(data_cfg)
    use_onchain = exp_cfg.get("features", {}).get("onchain_factors", False)
    gn_cfg = _glassnode_cfg(data_cfg)

    # Price
    from src.ingest.price import download_price
    logger.info(f"Downloading price data for {symbol} …")
    df = download_price(symbol, start, end, price_dir, force)
    logger.info(f"  ✓ Price: {len(df)} rows ({df.index[0].date()} → {df.index[-1].date()})")

    # On-chain (Iter-1+)
    if use_onchain:
        provider = onchain_cfg["onchain_provider"]
        metrics = onchain_cfg["resolved_metrics"]
        logger.info(f"Downloading on-chain metrics from {provider}: {metrics} …")
        if provider == "coinmetrics":
            from src.ingest.coinmetrics import load_coinmetrics

            oc = load_coinmetrics(
                metrics=metrics,
                asset=onchain_cfg["coinmetrics_asset"],
                frequency=onchain_cfg["coinmetrics_frequency"],
                start_time=onchain_cfg["coinmetrics_start_time"],
                end_time=onchain_cfg["coinmetrics_end_time"],
                cache_dir=onchain_cfg["resolved_cache_dir"],
                force=force,
            )
        else:
            from src.ingest.onchain import load_onchain

            oc = load_onchain(
                metrics=[str(m) for m in metrics if isinstance(m, str)] or None,
                timespan=onchain_cfg["onchain_timespan"],
                cache_dir=onchain_cfg["resolved_cache_dir"],
                force=force,
            )
        logger.info(f"  ✓ On-chain ({provider}): {len(oc)} rows, {oc.shape[1]} columns")
        if gn_cfg["use_glassnode"] and gn_cfg["glassnode_metrics"]:
            from src.ingest.glassnode import load_glassnode
            logger.info(
                f"Downloading Glassnode metrics: {len(gn_cfg['glassnode_metrics'])} configured …"
            )
            gn = load_glassnode(
                metrics=gn_cfg["glassnode_metrics"],
                cache_dir=gn_cfg["glassnode_cache_dir"],
                force=force,
                api_key_env=gn_cfg["glassnode_api_key_env"],
                asset=gn_cfg["glassnode_asset"],
                interval=gn_cfg["glassnode_interval"],
            )
            logger.info(f"  ✓ Glassnode: {len(gn)} rows, {gn.shape[1]} columns")

    click.secho("✓ download-data complete.", fg="green", bold=True)


# ── build-features ────────────────────────────────────────────

@cli.command("build-features")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--force", is_flag=True, default=False)
def build_features(config: str, data_config: str, force: bool):
    """Build feature + label dataset, save to data/features/."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    out_path = f"data/features/{_artifact_prefix(exp_cfg)}.parquet"

    from src.datasets.build_dataset import build_dataset
    df = build_dataset(**_build_dataset_kwargs(exp_cfg, data_cfg, force=force, output_path=out_path))
    logger.info(f"Dataset shape: {df.shape}")
    click.secho(f"✓ build-features complete → {out_path}", fg="green", bold=True)


@cli.command("show-search-space")
@click.option("--config", default="configs/experiment.yaml", show_default=True)
@click.option("--model", default=None, help=MODEL_HELP_TEXT)
@click.option(
    "--task",
    "task_name",
    type=click.Choice(TASK_CHOICES, case_sensitive=False),
    default=None,
    help=TASK_HELP_TEXT,
)
@click.option("--out", default=None, help="Optional markdown output path.")
def show_search_space(config: str, model: Optional[str], task_name: Optional[str], out: Optional[str]):
    """Print tuning candidate spaces so users do not need to inspect YAML manually."""
    exp_cfg = _load_exp_cfg(config)
    rows = _collect_search_space_rows(exp_cfg, model, task_name)
    if not rows:
        raise click.ClickException("No tuning search space found for the requested filters.")

    df = pd.DataFrame(rows)
    click.echo("\n── Tuning Search Space ──")
    current_model = None
    current_task = None
    for row in rows:
        if row["model"] != current_model or row["task"] != current_task:
            current_model = row["model"]
            current_task = row["task"]
            click.echo(f"\n[{current_model} | {current_task}]")
        click.echo(f"  {row['parameter']}: {row['candidate_space']}")

    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("# Tuning Search Space\n\n")
            f.write(_dataframe_to_markdown(df))
            f.write("\n")
        click.echo(f"\nSaved markdown → {out_path}")


# ── data-audit ───────────────────────────────────────────────

@cli.command("data-audit")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option(
    "--dataset-variant",
    default="all",
    type=click.Choice(DATASET_VARIANTS),
    help=DATASET_VARIANT_HELP_TEXT,
)
def data_audit(config: str, data_config: str, dataset_variant: str):
    """Run data quality audit and export CSV summaries."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    prefix = _artifact_prefix(exp_cfg)
    pred_cfg = data_cfg.get("prediction", {})
    split_cfg = data_cfg.get("split", {})

    feat_path = f"data/features/{_artifact_prefix(exp_cfg)}.parquet"
    if not Path(feat_path).exists():
        click.echo("Feature file not found, running build-features first …")
        from src.datasets.build_dataset import build_dataset

        _ = build_dataset(**_build_dataset_kwargs(exp_cfg, data_cfg, output_path=feat_path))

    df = pd.read_parquet(feat_path)
    from src.datasets.build_dataset import DIRECTION_LABEL_COL, get_feature_cols_by_variant
    from src.datasets.data_audit import run_data_audit, save_data_audit

    label_col = pred_cfg.get("target_col", "log_ret_h")
    cls_col = pred_cfg.get("classification_target_col", DIRECTION_LABEL_COL)
    feature_cols = get_feature_cols_by_variant(df, label_col=label_col, dataset_variant=dataset_variant)

    result = run_data_audit(
        df=df,
        label_col=label_col,
        classification_label_col=cls_col,
        feature_cols=feature_cols,
        train_ratio=float(split_cfg.get("train_ratio", 0.8)),
    )
    out_root = data_cfg.get("artifacts", {}).get("data_audit_dir", "reports/summary/data_audit")
    out_dir = Path(out_root) / prefix / dataset_variant
    paths = save_data_audit(result, out_dir)

    click.echo("\n── Data Audit Summary ──")
    click.echo(result.summary.to_string(index=False))
    click.echo("\n── Split Info ──")
    click.echo(result.split_info.to_string(index=False))
    click.echo("\n── Class Balance ──")
    click.echo(result.class_balance.to_string(index=False))
    click.echo("\nSaved files:")
    for k, p in paths.items():
        click.echo(f"  {k}: {p}")


# ── pipeline-prepare ──────────────────────────────────────────

@cli.command("pipeline-prepare")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--force", is_flag=True, default=False)
@click.option(
    "--dataset-variant",
    default="all",
    type=click.Choice(
        ["onchain", "ta", "all", "boruta_onchain", "boruta_ta", "boruta_all", "univariate"]
    ),
)
def pipeline_prepare(config: str, data_config: str, force: bool, dataset_variant: str):
    """
    Prepare data pipeline without model commitment:
    download -> build-features -> data-audit -> validate.
    """
    ctx = click.get_current_context()
    click.echo("\n[1/4] download-data")
    ctx.invoke(download_data, config=config, data_config=data_config, force=force)
    click.echo("\n[2/4] build-features")
    ctx.invoke(build_features, config=config, data_config=data_config, force=force)
    click.echo("\n[3/4] data-audit")
    ctx.invoke(data_audit, config=config, data_config=data_config, dataset_variant=dataset_variant)
    click.echo("\n[4/4] validate")
    ctx.invoke(validate, config=config, data_config=data_config)
    click.secho("\n✓ pipeline-prepare complete. Data foundation is ready for model selection.", fg="green", bold=True)


# ── tune ──────────────────────────────────────────────────────
# Main hyperparameter search entry.
# Typical usage:
#   - classification + boruta_onchain for directional chain-signal tests
#   - regression + boruta_onchain for return-forecast / trading-value tests
#   - show-search-space first if you need the exact candidate set

@cli.command("tune")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default=None, type=str, help=MODEL_HELP_TEXT)
@click.option(
    "--task",
    default=None,
    type=click.Choice(TASK_CHOICES),
    help=f"{TASK_HELP_TEXT} Default resolves from config.",
)
@click.option(
    "--dataset-variant",
    default=None,
    type=click.Choice(DATASET_VARIANTS),
    help=f"{DATASET_VARIANT_HELP_TEXT} Default resolves from config.",
)
@click.option("--trials", default=None, type=int, help="Override random-search trial count.")
@click.option("--metric", default=None, type=str, help="Objective metric. Default uses primary selection metric.")
@click.option("--apply-best/--no-apply-best", default=True, help="Write best params back to config.")
@click.option("--retrain-best/--no-retrain-best", default=True, help="Run train again with best params.")
@click.option("--run-backtest/--no-run-backtest", default=True, help="Run backtest after retraining.")
@click.option("--run-report/--no-run-report", default=True, help="Run report after backtest.")
def tune(
    config: str,
    data_config: str,
    model_name: Optional[str],
    task: Optional[str],
    dataset_variant: Optional[str],
    trials: Optional[int],
    metric: Optional[str],
    apply_best: bool,
    retrain_best: bool,
    run_backtest: bool,
    run_report: bool,
):
    """Random-search hyperparameter tuning on a chronological validation split."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    resolved_model_name = _resolve_selected_model(model_name, exp_cfg)
    task_name = _resolve_task(task, exp_cfg, data_cfg)
    variant_name = _resolve_dataset_variant(dataset_variant, exp_cfg)

    df = _load_or_build_feature_dataset(exp_cfg, data_cfg)
    label_col, feature_cols = _resolve_feature_cols_for_variant(
        df=df,
        task_name=task_name,
        variant_name=variant_name,
        exp_cfg=exp_cfg,
        data_cfg=data_cfg,
    )

    ModelCls, base_model_cfg = _resolve_model(
        resolved_model_name,
        exp_cfg.get("models", {}),
        task=task_name,
        exp_cfg=exp_cfg,
        variant_name=variant_name,
    )
    train_df, val_df = _split_final_fit_data(
        df=df,
        feature_cols=feature_cols,
        label_col=label_col,
        val_months=float(data_cfg.get("split", {}).get("val_months", 6)),
    )
    if len(val_df) == 0:
        raise click.ClickException("Validation split is empty. Tuning requires a non-empty validation window.")

    tuning_cfg = exp_cfg.get("tuning", {})
    n_trials = int(trials or tuning_cfg.get("n_trials", 20))
    objective = str(metric or _default_tuning_metric(task_name, exp_cfg)).lower()
    search_space = _resolve_tuning_space(exp_cfg, resolved_model_name, task_name)
    if not search_space:
        raise click.ClickException(
            f"No tuning search space configured for model={resolved_model_name}, task={task_name}."
        )

    rng = random.Random(int(tuning_cfg.get("random_state", exp_cfg.get("random_seed", 42))))
    tuning_root = _tuning_root(exp_cfg)
    stem = f"{_artifact_prefix(exp_cfg)}_{resolved_model_name}_{task_name}_{variant_name}"
    trials_path = tuning_root / f"{stem}_trials.csv"
    best_path = tuning_root / f"{stem}_best.json"

    click.echo(
        f"\n── Hyperparameter Tuning ──\n"
        f"  model={resolved_model_name}\n"
        f"  task={task_name}\n"
        f"  dataset_variant={variant_name}\n"
        f"  features={len(feature_cols)}\n"
        f"  train_rows={len(train_df)}\n"
        f"  val_rows={len(val_df)}\n"
        f"  objective={objective}\n"
        f"  trials={n_trials}"
    )

    rows: list[dict] = []
    best_score = float("-inf")
    best_row: dict | None = None

    for trial_idx in range(1, n_trials + 1):
        trial_cfg = _sample_param_config(base_model_cfg, search_space, rng, trial_idx)
        metrics, y_pred = _evaluate_model_config(
            model_cls=ModelCls,
            model_config=trial_cfg,
            train_df=train_df,
            val_df=val_df,
            feature_cols=feature_cols,
            label_col=label_col,
            task_name=task_name,
            metric_prefix_name=resolved_model_name,
        )
        metric_key = f"{resolved_model_name}_{task_name}_val_{objective}"
        if metric_key not in metrics and objective == "directional_accuracy":
            metric_value = float(
                np.mean(
                    (np.asarray(val_df[label_col].values) > 0).astype(int)
                    == (np.asarray(y_pred) > 0).astype(int)
                )
            )
            metrics[metric_key] = metric_value
        elif metric_key not in metrics:
            raise click.ClickException(
                f"Objective metric '{objective}' not available for model={resolved_model_name}, task={task_name}."
            )
        metric_value = float(metrics[metric_key])
        score = _score_metric(objective, metric_value)
        row = {
            "trial": trial_idx,
            "model": resolved_model_name,
            "task": task_name,
            "dataset_variant": variant_name,
            "objective": objective,
            "objective_value": metric_value,
            "score": score,
            "feature_count": len(feature_cols),
            "train_rows": len(train_df),
            "val_rows": len(val_df),
            "params_json": json.dumps(trial_cfg, ensure_ascii=False, sort_keys=True),
        }
        row.update(metrics)
        rows.append(row)

        if score > best_score:
            best_score = score
            best_row = {
                "trial": trial_idx,
                "model": resolved_model_name,
                "task": task_name,
                "dataset_variant": variant_name,
                "objective": objective,
                "objective_value": metric_value,
                "score": score,
                "params": trial_cfg,
                "metrics": metrics,
            }
            click.echo(
                f"  [{trial_idx}/{n_trials}] new best: {objective}={metric_value:.6f} "
                f"(score={score:.6f})"
            )
        else:
            click.echo(
                f"  [{trial_idx}/{n_trials}] {objective}={metric_value:.6f} "
                f"(best={best_row['objective_value']:.6f})"
            )

    trials_df = pd.DataFrame(rows).sort_values("score", ascending=False)
    trials_df.to_csv(trials_path, index=False, encoding="utf-8")
    with open(best_path, "w", encoding="utf-8") as f:
        json.dump(best_row, f, indent=2, ensure_ascii=False)

    if apply_best and best_row is not None:
        _write_best_params_to_config(
            config_path=config,
            exp_cfg=exp_cfg,
            model_name=resolved_model_name,
            task_name=task_name,
            variant_name=variant_name,
            params=best_row["params"],
            objective=objective,
            objective_value=float(best_row["objective_value"]),
        )
        click.echo(f"  applied best params to {config} :: tuning.best_params.{resolved_model_name}.{task_name}.{variant_name}")

    if retrain_best:
        train_cmd = [
            sys.executable,
            "-m",
            "src.cli",
            "train",
            "--config",
            config,
            "--data-config",
            data_config,
            "--model",
            resolved_model_name,
            "--task",
            task_name,
            "--dataset-variant",
            variant_name,
        ]
        _run_followup_cli_step(train_cmd, "retrain-best")
        if run_backtest:
            backtest_cmd = [
                sys.executable,
                "-m",
                "src.cli",
                "backtest",
                "--config",
                config,
                "--data-config",
                data_config,
                "--model",
                resolved_model_name,
                "--task",
                task_name,
                "--dataset-variant",
                variant_name,
            ]
            _run_followup_cli_step(backtest_cmd, "backtest-best")
            if run_report:
                report_cmd = [
                    sys.executable,
                    "-m",
                    "src.cli",
                    "report",
                    "--config",
                    config,
                    "--data-config",
                    data_config,
                    "--model",
                    resolved_model_name,
                    "--task",
                    task_name,
                    "--dataset-variant",
                    variant_name,
                ]
                _run_followup_cli_step(report_cmd, "report-best")

    click.secho(
        f"\n✓ tuning complete → {trials_path}\n"
        f"  best_config={best_path}",
        fg="green",
        bold=True,
    )


# ── train ─────────────────────────────────────────────────────
# Main OOS experiment command.
# This is the command that generates walk-forward predictions used later by:
#   - backtest
#   - report
#   - halving-strategy-study
# If you care about paper-grade results, this command is usually the source of truth.

@cli.command("train")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default=None, type=str, help=MODEL_HELP_TEXT)
@click.option(
    "--task",
    default=None,
    type=click.Choice(TASK_CHOICES),
    help=f"{TASK_HELP_TEXT} Default resolves from config.",
)
@click.option(
    "--dataset-variant",
    default=None,
    type=click.Choice(DATASET_VARIANTS),
    help=f"{DATASET_VARIANT_HELP_TEXT} Default resolves from config.",
)
def train(
    config: str,
    data_config: str,
    model_name: Optional[str],
    task: Optional[str],
    dataset_variant: Optional[str],
):
    """Run walk-forward training and save predictions."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    exp_name = exp_cfg["experiment_name"]
    prefix = _artifact_prefix(exp_cfg)
    symbol = exp_cfg.get("symbol", "BTC-USD")
    split_cfg = data_cfg.get("split", {})
    pred_cfg = data_cfg.get("prediction", {})
    horizon = int(pred_cfg.get("horizon", 7))
    seed = int(data_cfg.get("random_seed", 42))
    task_name = _resolve_task(task, exp_cfg, data_cfg)
    resolved_model_name = _resolve_selected_model(model_name, exp_cfg)
    variant_name = _resolve_dataset_variant(dataset_variant, exp_cfg)
    label_col = _resolve_label_col(task_name, exp_cfg, data_cfg)
    np.random.seed(seed)

    df = _load_or_build_feature_dataset(exp_cfg, data_cfg)

    from src.evaluation.ic_diagnostics import (
        generate_ic_figures,
        sample_alignment_rows,
        summarize_ic,
        upsert_rows,
    )
    from src.evaluation.walk_forward import fold_results_to_table, run_walk_forward
    from src.evaluation.metrics import (
        compute_classification_metrics,
        compute_metrics,
        rank_ic,
    )

    label_col, feature_cols = _resolve_feature_cols_for_variant(
        df=df,
        task_name=task_name,
        variant_name=variant_name,
        exp_cfg=exp_cfg,
        data_cfg=data_cfg,
    )
    logger.info(f"Feature count ({variant_name}): {len(feature_cols)}")

    ModelCls, model_cfg = _resolve_model(
        resolved_model_name,
        exp_cfg.get("models", {}),
        task=task_name,
        exp_cfg=exp_cfg,
        variant_name=variant_name,
    )

    fold_results, pred_df = _run_walk_forward_compat(
        run_walk_forward,
        df=df,
        feature_cols=feature_cols,
        label_col=label_col,
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
    metric_prefix = f"{resolved_model_name}_{task_name}_oos"
    if task_name == "classification":
        all_metrics = compute_classification_metrics(
            pred_df["y_true"].values,
            pred_df["y_pred"].values,
            prefix=metric_prefix,
            threshold=0.5,
        )
    else:
        all_metrics = compute_metrics(
            pred_df["y_true"].values,
            pred_df["y_pred"].values,
            prefix=metric_prefix,
        )
        ric = rank_ic(pred_df["y_true"].values, pred_df["y_pred"].values)
        all_metrics[f"{resolved_model_name}_oos_rank_ic"] = ric

    click.echo("\n── Out-of-sample metrics ──")
    for k, v in all_metrics.items():
        click.echo(f"  {k}: {v:.4f}")

    # ── Save predictions ───────────────────────────────────────
    pred_out = (
        f"data/features/{prefix}_{resolved_model_name}_"
        f"{task_name}_{variant_name}_preds.parquet"
    )
    pred_df.to_parquet(pred_out)
    logger.info(f"Predictions saved → {pred_out}")

    # ── Save metrics ───────────────────────────────────────────
    metrics_out = (
        f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_metrics.json"
    )
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)

    # ── Save per-fold diagnostics table ────────────────────────
    ic_table = fold_results_to_table(
        fold_results=fold_results,
        config_name=f"{exp_name}:{task_name}:{variant_name}",
        model_name=resolved_model_name,
    )
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    ic_path = reports_dir / "ic_table.csv"
    key_cols = ["config_name", "model_name", "fold_id"]
    ic_table = upsert_rows(ic_path, ic_table, key_cols)
    ic_table = ic_table.sort_values(key_cols)
    ic_table.to_csv(ic_path, index=False, encoding="utf-8")
    logger.info(f"IC table saved → {ic_path}")

    # ── Save diagnostics table ────────────────────────────────
    diag_table = ic_table.copy()
    diag_table["ic_negative"] = diag_table["IC"] < 0
    diag_path = reports_dir / "ic_diagnostics.csv"
    diag_table = upsert_rows(diag_path, diag_table, key_cols)
    diag_table = diag_table.sort_values(key_cols)
    diag_table.to_csv(diag_path, index=False, encoding="utf-8")
    logger.info(f"IC diagnostics saved → {diag_path}")

    # ── Print IC diagnostics summary for current run ──────────
    run_diag = diag_table[
        (diag_table["config_name"] == f"{exp_name}:{task_name}:{variant_name}")
        & (diag_table["model_name"] == resolved_model_name)
    ]
    stats = summarize_ic(run_diag)
    click.echo("\n── IC diagnostics summary ──")
    click.echo(f"  IC_mean: {stats['IC_mean']:.6f}")
    click.echo(f"  IC_median: {stats['IC_median']:.6f}")
    click.echo(f"  IC_std: {stats['IC_std']:.6f}")
    click.echo(f"  IC_negative_ratio: {stats['IC_negative_ratio']:.6f}")
    click.echo(f"  Best fold IC: {stats['best_fold_ic']:.6f}")
    click.echo(f"  Worst fold IC: {stats['worst_fold_ic']:.6f}")

    # ── Alignment sanity check (regression only) ──────────────
    if task_name == "regression":
        required_cols = {
            "y_pred",
            "y_true",
            "close_t",
            "close_t_plus_h",
            "manual_log_return",
            "alignment_abs_err",
        }
        if required_cols.issubset(set(pred_df.columns)):
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
        else:
            click.echo("\n── Alignment sanity check skipped (required columns unavailable) ──")

    # ── Generate Matplotlib diagnostics figures ───────────────
    generated = generate_ic_figures(diag_table, reports_dir)
    if generated:
        for fp in generated:
            logger.info(f"IC diagnostic figure → {fp}")

    # ── Save final full-fit model for deployment/latest prediction ──
    final_model, final_train_df, final_val_df = _fit_final_model(
        df=df,
        feature_cols=feature_cols,
        label_col=label_col,
        model_cls=ModelCls,
        model_config=model_cfg,
        val_months=float(split_cfg.get("val_months", 6)),
    )
    final_model_path, final_meta_path = _model_artifact_paths(
        exp_cfg=exp_cfg,
        model_name=resolved_model_name,
        task_name=task_name,
        variant_name=variant_name,
    )
    final_model.save(final_model_path)
    final_meta = {
        "experiment_name": exp_name,
        "artifact_prefix": prefix,
        "symbol": symbol,
        "model": resolved_model_name,
        "task": task_name,
        "dataset_variant": variant_name,
        "label_col": label_col,
        "feature_cols": feature_cols,
        "feature_count": len(feature_cols),
        "train_rows": len(final_train_df),
        "validation_rows": len(final_val_df),
        "train_start": final_train_df.index.min().date().isoformat(),
        "train_end": final_train_df.index.max().date().isoformat(),
        "validation_start": (
            final_val_df.index.min().date().isoformat() if len(final_val_df) else None
        ),
        "validation_end": (
            final_val_df.index.max().date().isoformat() if len(final_val_df) else None
        ),
        "saved_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "config_path": config,
        "data_config_path": data_config,
        "model_config": model_cfg,
    }
    with open(final_meta_path, "w", encoding="utf-8") as f:
        json.dump(final_meta, f, indent=2, ensure_ascii=False)
    logger.info(f"Final model saved → {final_model_path}")
    logger.info(f"Final model metadata saved → {final_meta_path}")

    click.secho(
        f"\n✓ train complete → {pred_out}\n"
        f"  task={task_name}, dataset_variant={variant_name}, label={label_col}, model={resolved_model_name}\n"
        f"  final_model={final_model_path}",
        fg="green",
        bold=True,
    )


# ── predict-latest ───────────────────────────────────────────

@cli.command("predict-latest")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default=None, type=str, help=MODEL_HELP_TEXT)
@click.option(
    "--task",
    default=None,
    type=click.Choice(TASK_CHOICES),
    help=f"{TASK_HELP_TEXT} Default: run all enabled tasks.",
)
@click.option(
    "--dataset-variant",
    default=None,
    type=click.Choice(DATASET_VARIANTS),
    help=f"{DATASET_VARIANT_HELP_TEXT} Default resolves from config.",
)
@click.option("--force", is_flag=True, default=False, help="Force re-download/rebuild latest data.")
def predict_latest(
    config: str,
    data_config: str,
    model_name: Optional[str],
    task: Optional[str],
    dataset_variant: Optional[str],
    force: bool,
):
    """Fit on full history and predict the latest available row."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    resolved_model_name = _resolve_selected_model(model_name, exp_cfg)
    variant_name = _resolve_dataset_variant(dataset_variant, exp_cfg)
    df = _load_or_build_feature_dataset(
        exp_cfg,
        data_cfg,
        force=force,
        keep_unlabeled_tail=True,
    )

    tasks_to_run: list[str]
    if task:
        tasks_to_run = [task]
    else:
        tasks_cfg = exp_cfg.get("tasks", {})
        tasks_to_run = [
            name for name in ("classification", "regression")
            if tasks_cfg.get(name, {}).get("enabled", False)
        ] or ["regression"]

    split_cfg = data_cfg.get("split", {})
    out_dir = Path("reports/summary/latest_predictions")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for task_name in tasks_to_run:
        label_col, feature_cols = _resolve_feature_cols_for_variant(
            df=df,
            task_name=task_name,
            variant_name=variant_name,
            exp_cfg=exp_cfg,
            data_cfg=data_cfg,
        )
        ModelCls, model_cfg = _resolve_model(
            resolved_model_name,
            exp_cfg.get("models", {}),
            task=task_name,
            exp_cfg=exp_cfg,
            variant_name=variant_name,
        )
        model_path, meta_path = _model_artifact_paths(
            exp_cfg=exp_cfg,
            model_name=resolved_model_name,
            task_name=task_name,
            variant_name=variant_name,
        )

        feature_ready = df.dropna(subset=feature_cols).copy()
        if feature_ready.empty:
            raise RuntimeError(
                f"No feature-complete rows available for latest prediction ({task_name}, {variant_name})."
            )
        latest_row = feature_ready.iloc[[-1]].copy()
        predict_date = pd.Timestamp(latest_row.index[-1])

        labeled = (
            df.loc[df.index < predict_date]
            .dropna(subset=feature_cols + [label_col])
            .copy()
        )
        if model_path.exists() and meta_path.exists() and not force:
            model = ModelCls.load(model_path)
            meta = _read_json_file(meta_path)
            feature_cols = list(meta.get("feature_cols", feature_cols))
            train_rows = int(meta.get("train_rows", 0))
            val_rows = int(meta.get("validation_rows", 0))
        else:
            model, train_df, val_df = _fit_final_model(
                df=labeled,
                feature_cols=feature_cols,
                label_col=label_col,
                model_cls=ModelCls,
                model_config=model_cfg,
                val_months=float(split_cfg.get("val_months", 6)),
            )
            train_rows = int(len(train_df))
            val_rows = int(len(val_df))
        pred_value = float(model.predict(latest_row[feature_cols])[0])

        if task_name == "classification":
            predicted_direction = "up" if pred_value >= 0.5 else "down"
            score_name = "up_probability"
        else:
            predicted_direction = "up" if pred_value > 0 else "down"
            score_name = "predicted_log_return"

        row = {
            "task": task_name,
            "model": resolved_model_name,
            "dataset_variant": variant_name,
            "predict_date": predict_date.date().isoformat(),
            "trained_rows": train_rows,
            "validation_rows": val_rows,
            "feature_count": int(len(feature_cols)),
            "predicted_direction": predicted_direction,
            score_name: pred_value,
            "model_artifact": str(model_path) if model_path.exists() else None,
        }
        rows.append(row)

    result_df = pd.DataFrame(rows)
    timestamp = pd.Timestamp.now(tz="UTC").strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"{_artifact_prefix(exp_cfg)}_latest_{resolved_model_name}_{variant_name}_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    click.echo("\n── Latest Prediction ──")
    click.echo(result_df.to_string(index=False))
    click.echo(f"\nSaved JSON: {out_path}")


# ── test-full-history ────────────────────────────────────────
# Full-history scoring command.
# Use this only when you want to score the saved final model on the whole
# labeled history. It is useful for sanity checks, but it is not the same
# as strict walk-forward OOS evaluation.

@cli.command("test-full-history")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default=None, type=str, help=MODEL_HELP_TEXT)
@click.option(
    "--task",
    default=None,
    type=click.Choice(TASK_CHOICES),
    help=f"{TASK_HELP_TEXT} Default resolves from config.",
)
@click.option(
    "--dataset-variant",
    default=None,
    type=click.Choice(DATASET_VARIANTS),
    help=f"{DATASET_VARIANT_HELP_TEXT} Default resolves from config.",
)
@click.option(
    "--cost-bps",
    default=None,
    type=float,
    help="Optional single transaction cost to print first. Full sensitivity table is always saved.",
)
def test_full_history(
    config: str,
    data_config: str,
    model_name: Optional[str],
    task: Optional[str],
    dataset_variant: Optional[str],
    cost_bps: Optional[float],
):
    """Score the full labeled history with the saved final model and backtest it."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    prefix = _artifact_prefix(exp_cfg)
    symbol = exp_cfg.get("symbol", "BTC-USD")
    task_name = _resolve_task(task, exp_cfg, data_cfg)
    resolved_model_name = _resolve_selected_model(model_name, exp_cfg)
    variant_name = _resolve_dataset_variant(dataset_variant, exp_cfg)

    from src.evaluation.metrics import compute_classification_metrics, compute_metrics, rank_ic
    from src.backtest.strategy import make_signal
    from src.backtest.backtester import run_backtest, sensitivity_analysis
    from src.ingest.price import download_price
    from src.etl.cleaner import clean_price

    ModelCls, _ = _resolve_model(
        resolved_model_name,
        exp_cfg.get("models", {}),
        task=task_name,
        exp_cfg=exp_cfg,
        variant_name=variant_name,
    )
    model_path, meta_path = _model_artifact_paths(
        exp_cfg=exp_cfg,
        model_name=resolved_model_name,
        task_name=task_name,
        variant_name=variant_name,
    )
    if not model_path.exists():
        raise click.ClickException(
            f"Saved final model not found: {model_path}. Run 'train' first."
        )

    df = _load_or_build_feature_dataset(exp_cfg, data_cfg, keep_unlabeled_tail=False)
    label_col, feature_cols = _resolve_feature_cols_for_variant(
        df=df,
        task_name=task_name,
        variant_name=variant_name,
        exp_cfg=exp_cfg,
        data_cfg=data_cfg,
    )

    if meta_path.exists():
        meta = _read_json_file(meta_path)
        feature_cols = list(meta.get("feature_cols", feature_cols))
        label_col = str(meta.get("label_col", label_col))

    hist_df = df.dropna(subset=feature_cols + [label_col]).copy()
    if hist_df.empty:
        raise click.ClickException(
            f"No labeled, feature-complete rows available for full-history test ({resolved_model_name}, {task_name}, {variant_name})."
        )

    model = ModelCls.load(model_path)
    _prepare_model_for_history_scoring(model)
    y_pred = model.predict(hist_df[feature_cols])
    pred_df = pd.DataFrame(
        {
            "y_true": hist_df[label_col].astype(float).values,
            "y_pred": np.asarray(y_pred, dtype=float),
        },
        index=hist_df.index,
    )
    pred_df.index.name = "date"

    metric_prefix = f"{resolved_model_name}_{task_name}_full_history"
    if task_name == "classification":
        all_metrics = compute_classification_metrics(
            pred_df["y_true"].values,
            pred_df["y_pred"].values,
            prefix=metric_prefix,
            threshold=0.5,
        )
    else:
        all_metrics = compute_metrics(
            pred_df["y_true"].values,
            pred_df["y_pred"].values,
            prefix=metric_prefix,
        )
        all_metrics[f"{resolved_model_name}_{task_name}_full_history_rank_ic"] = rank_ic(
            pred_df["y_true"].values,
            pred_df["y_pred"].values,
        )

    pred_out = (
        f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_full_history_preds.parquet"
    )
    metrics_out = (
        f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_full_history_metrics.json"
    )
    pred_df.to_parquet(pred_out)
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)

    price_df = clean_price(
        download_price(
            symbol,
            data_cfg["price"]["start_date"],
            data_cfg["price"].get("end_date"),
            data_cfg["price"]["cache_dir"],
        )
    )

    strat_cfg = exp_cfg.get("strategy", {})
    signal_scores = pred_df["y_pred"].astype(float) - 0.5 if task_name == "classification" else pred_df["y_pred"].astype(float)
    signal = make_signal(
        signal_scores,
        mode=strat_cfg.get("mode", "long_only"),
        top_quantile=float(strat_cfg.get("top_quantile", 0.2)),
        bottom_quantile=float(strat_cfg.get("bottom_quantile", 0.2)),
    )
    costs = [float(v) for v in strat_cfg.get("cost_bps", [5.0, 10.0, 20.0])]
    bt_table = sensitivity_analysis(price_df, signal, cost_bps_list=costs)
    bt_out = (
        f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_full_history_backtest_sensitivity.csv"
    )
    bt_table.reset_index().to_csv(bt_out, index=False, encoding="utf-8")

    preferred_cost = float(cost_bps) if cost_bps is not None else float(strat_cfg.get("default_cost_bps", costs[0]))
    bt_single = run_backtest(price_df, signal, cost_bps=preferred_cost)
    equity_out = (
        f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_full_history_equity.parquet"
    )
    pd.DataFrame({"equity": bt_single["equity"]}).to_parquet(equity_out)

    click.echo("\n── Full-History Predictive Metrics (in-sample / full-history) ──")
    for k, v in all_metrics.items():
        click.echo(f"  {k}: {v:.4f}")

    click.echo("\n── Full-History Backtest Sensitivity ──")
    click.echo(bt_table.to_string(float_format=lambda x: f"{x:.6f}"))
    click.echo(
        "\nNOTE: this command reuses the final saved model on the full labeled history. "
        "It is not out-of-sample and should be treated as an upper-bound / overfitting check."
    )
    click.secho(
        f"\n✓ full-history test complete → {pred_out}\n"
        f"  metrics={metrics_out}\n"
        f"  backtest={bt_out}\n"
        f"  equity={equity_out}",
        fg="green",
        bold=True,
    )


@cli.command("halving-strategy-study")
# Stability / strategy-mapping study on saved predictions.
# It keeps the model fixed and only changes:
#   1. period slices (full sample + fixed halving cycles)
#   2. signal / exposure mapping rules
# This is where you test whether a model's prediction signal is better as
# long_only, full_exposure_sign, or quantile-based selective trading.
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default=None, type=str, help=MODEL_HELP_TEXT)
@click.option(
    "--task",
    default=None,
    type=click.Choice(TASK_CHOICES),
    help=f"{TASK_HELP_TEXT} Default resolves from config.",
)
@click.option(
    "--dataset-variant",
    default=None,
    type=click.Choice(DATASET_VARIANTS),
    help=f"{DATASET_VARIANT_HELP_TEXT} Default resolves from config.",
)
@click.option("--cost-bps", default=5.0, type=float, show_default=True)
@click.option(
    "--prediction-scope",
    default="oos",
    type=click.Choice(["oos", "full_history"]),
    show_default=True,
    help="Use existing OOS predictions or full-history predictions from test-full-history.",
)
def halving_strategy_study(
    config: str,
    data_config: str,
    model_name: Optional[str],
    task: Optional[str],
    dataset_variant: Optional[str],
    cost_bps: float,
    prediction_scope: str,
):
    """Evaluate fixed halving periods and fixed strategy search space on saved predictions."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)
    prefix = _artifact_prefix(exp_cfg)
    symbol = exp_cfg.get("symbol", "BTC-USD")
    task_name = _resolve_task(task, exp_cfg, data_cfg)
    resolved_model_name = _resolve_selected_model(model_name, exp_cfg)
    variant_name = _resolve_dataset_variant(dataset_variant, exp_cfg)

    from src.backtest.backtester import run_backtest
    from src.ingest.price import download_price
    from src.etl.cleaner import clean_price

    suffix = "_full_history_preds.parquet" if prediction_scope == "full_history" else "_preds.parquet"
    pred_path = Path(f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}{suffix}")
    if not pred_path.exists():
        raise click.ClickException(
            f"Prediction file not found: {pred_path}. "
            f"Run 'train' first for OOS, or 'test-full-history' for full_history."
        )

    pred_df = pd.read_parquet(pred_path)
    if pred_df.empty:
        raise click.ClickException(f"Prediction file is empty: {pred_path}")
    pred_df.index = pd.DatetimeIndex(pred_df.index)
    if pred_df.index.tz is None:
        pred_df.index = pred_df.index.tz_localize("UTC")
    else:
        pred_df.index = pred_df.index.tz_convert("UTC")

    price_df = clean_price(
        download_price(
            symbol,
            data_cfg["price"]["start_date"],
            data_cfg["price"].get("end_date"),
            data_cfg["price"]["cache_dir"],
        )
    )

    prediction_start = pd.Timestamp(pred_df.index.min())
    if prediction_start.tzinfo is None:
        prediction_start = prediction_start.tz_localize("UTC")
    else:
        prediction_start = prediction_start.tz_convert("UTC")

    scores = pred_df["y_pred"].astype(float) - 0.5 if task_name == "classification" else pred_df["y_pred"].astype(float)
    periods = _fixed_halving_periods(price_df.index.max())
    strategy_specs = _fixed_strategy_specs()

    out_dir = Path("reports/summary/stability")
    out_dir.mkdir(parents=True, exist_ok=True)
    strategy_rows: list[dict] = []
    period_rows: list[dict] = []

    for spec in strategy_specs:
        signal = _signal_from_strategy_spec(scores, spec)
        full_res = run_backtest(price_df, signal, cost_bps=cost_bps)
        strategy_rows.append(
            {
                "prediction_scope": prediction_scope,
                "model": resolved_model_name,
                "task": task_name,
                "variant": variant_name,
                "strategy": str(spec["name"]),
                "prediction_start": prediction_start.date().isoformat(),
                "cost_bps": float(cost_bps),
                "exposure_rate": float((signal != 0).mean()),
                "long_rate": float((signal > 0).mean()),
                "short_rate": float((signal < 0).mean()),
                "cumulative_return": float(full_res["cumulative_return"]),
                "annualised_return": float(full_res["annualised_return"]),
                "sharpe_ratio": float(full_res["sharpe_ratio"]),
                "max_drawdown": float(full_res["max_drawdown"]),
                "turnover": float(full_res["turnover"]),
                "n_days": int(full_res["n_days"]),
            }
        )

        for period_name, start_ts, end_ts in periods:
            px = price_df.loc[(price_df.index >= start_ts) & (price_df.index <= end_ts)].copy()
            sg = signal.loc[(signal.index >= start_ts) & (signal.index <= end_ts)].copy()
            if px.empty or sg.empty:
                continue
            effective_start = max(start_ts, prediction_start)
            res = run_backtest(px, sg, cost_bps=cost_bps)
            period_rows.append(
                {
                    "prediction_scope": prediction_scope,
                    "model": resolved_model_name,
                    "task": task_name,
                    "variant": variant_name,
                    "strategy": str(spec["name"]),
                    "period": period_name,
                    "period_start": start_ts.date().isoformat(),
                    "period_end": end_ts.date().isoformat(),
                    "prediction_start": prediction_start.date().isoformat(),
                    "effective_strategy_start": effective_start.date().isoformat(),
                    "cost_bps": float(cost_bps),
                    "exposure_rate": float((sg != 0).mean()),
                    "long_rate": float((sg > 0).mean()),
                    "short_rate": float((sg < 0).mean()),
                    "cumulative_return": float(res["cumulative_return"]),
                    "annualised_return": float(res["annualised_return"]),
                    "sharpe_ratio": float(res["sharpe_ratio"]),
                    "max_drawdown": float(res["max_drawdown"]),
                    "turnover": float(res["turnover"]),
                    "n_days": int(res["n_days"]),
                }
            )

    strategy_df = pd.DataFrame(strategy_rows).sort_values(
        ["cumulative_return", "sharpe_ratio"],
        ascending=False,
    ).reset_index(drop=True)
    period_df = pd.DataFrame(period_rows).sort_values(
        ["strategy", "period_start"],
    ).reset_index(drop=True)

    stem = f"{prefix}_{resolved_model_name}_{task_name}_{variant_name}_{prediction_scope}"
    strategy_csv = out_dir / f"{stem}_strategy_search.csv"
    period_csv = out_dir / f"{stem}_halving_periods.csv"
    summary_md = out_dir / f"{stem}_halving_strategy_summary.md"
    strategy_df.to_csv(strategy_csv, index=False, encoding="utf-8")
    period_df.to_csv(period_csv, index=False, encoding="utf-8")

    best_by_return = strategy_df.iloc[0]
    best_by_sharpe = strategy_df.sort_values(
        ["sharpe_ratio", "cumulative_return"],
        ascending=False,
    ).iloc[0]
    with open(summary_md, "w", encoding="utf-8") as f:
        f.write("# Halving Period and Strategy Study\n\n")
        f.write(f"- model: `{resolved_model_name}`\n")
        f.write(f"- task: `{task_name}`\n")
        f.write(f"- dataset_variant: `{variant_name}`\n")
        f.write(f"- prediction_scope: `{prediction_scope}`\n")
        f.write(f"- prediction_start: `{prediction_start.date().isoformat()}`\n")
        f.write(f"- cost_bps: `{cost_bps}`\n\n")
        f.write("## Best by Cumulative Return\n\n")
        f.write(_dataframe_to_markdown(pd.DataFrame([best_by_return])))
        f.write("\n\n## Best by Sharpe\n\n")
        f.write(_dataframe_to_markdown(pd.DataFrame([best_by_sharpe])))
        f.write("\n\n## Fixed Halving Periods\n\n")
        f.write(f"- `full_sample` (strategy active from `{prediction_start.date().isoformat()}`)\n")
        f.write("- `2016-07-09 ~ 2020-05-10`\n")
        f.write("- `2020-05-11 ~ 2024-04-19`\n")
        f.write("- `2024-04-20 ~ end`\n")

    click.echo("\n── Halving Strategy Study ──")
    click.echo(strategy_df.head(10).to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    click.secho(
        f"\n✓ halving-strategy-study complete\n"
        f"  strategy_search={strategy_csv}\n"
        f"  halving_periods={period_csv}\n"
        f"  summary={summary_md}",
        fg="green",
        bold=True,
    )


# ── horizon-sweep ────────────────────────────────────────────

@cli.command("horizon-sweep")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default="lgbm",
              type=click.Choice(["ridge", "lasso", "lgbm", "svm", "rf"]))
def horizon_sweep(config: str, data_config: str, model_name: str):
    """Run horizon sensitivity study and export structured diagnostics."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    horizons = exp_cfg.get("evaluation", {}).get("horizons")
    if not horizons:
        horizons = [1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90, 120, 180]
    horizons = [int(h) for h in horizons]

    split_cfg = data_cfg.get("split", {})
    ModelCls, model_cfg = _resolve_model(model_name, exp_cfg.get("models", {}), task="regression")

    from src.datasets.build_dataset import LABEL_COL, build_dataset, get_feature_cols
    from src.evaluation.walk_forward import run_walk_forward

    rows: list[dict] = []
    for h in horizons:
        ds_kwargs = _build_dataset_kwargs(exp_cfg, data_cfg, output_path=None)
        ds_kwargs["horizon"] = h
        ds_kwargs["label_horizon_days"] = h
        df = build_dataset(**ds_kwargs)
        feature_cols = get_feature_cols(df, LABEL_COL)
        fold_results, _ = _run_walk_forward_compat(
            run_walk_forward,
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

    out_csv = Path("reports/summary/model_level/horizon_sweep_summary.csv")
    out_fig_dir = Path("reports/summary/model_level/figures")
    out_md = Path("reports/summary/horizon_sweep_summary.md")
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
@click.option("--config", default="configs/experiment.yaml")
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

    split_cfg = data_cfg.get("split", {})

    from src.datasets.build_dataset import LABEL_COL, build_dataset, get_feature_cols
    from src.evaluation.metrics import ic, rank_ic
    from src.evaluation.walk_forward import generate_folds

    rows: list[dict] = []
    for h in horizons:
        ds_kwargs = _build_dataset_kwargs(exp_cfg, data_cfg, output_path=None)
        ds_kwargs["horizon"] = h
        ds_kwargs["label_horizon_days"] = h
        df = build_dataset(**ds_kwargs)
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
    out_csv = Path("reports/summary/feature_level/feature_horizon_ic_matrix.csv")
    out_fig_dir = Path("reports/summary/feature_level/figures")
    out_md = Path("reports/summary/feature_horizon_matrix_summary.md")
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


# ── stability-regime ────────────────────────────────────────

@cli.command("stability-regime")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default="lgbm",
              type=click.Choice(["ridge", "lasso", "lgbm", "svm", "rf"]))
@click.option("--rolling-window", default=180, type=int)
def stability_regime(
    config: str, data_config: str, model_name: str, rolling_window: int
):
    """Run rolling stability and market-regime diagnostics."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)
    split_cfg = data_cfg.get("split", {})
    pred_cfg = data_cfg.get("prediction", {})
    horizon = int(pred_cfg.get("horizon", 7))

    from src.datasets.build_dataset import LABEL_COL, build_dataset, get_feature_cols
    from src.evaluation.metrics import ic, rank_ic
    from src.evaluation.walk_forward import run_walk_forward

    ModelCls, model_cfg = _resolve_model(model_name, exp_cfg.get("models", {}), task="regression")
    ds_kwargs = _build_dataset_kwargs(exp_cfg, data_cfg, output_path=None)
    ds_kwargs["horizon"] = horizon
    ds_kwargs["label_horizon_days"] = horizon
    df = build_dataset(**ds_kwargs)
    feature_cols = get_feature_cols(df, LABEL_COL)
    _, pred_df = _run_walk_forward_compat(
        run_walk_forward,
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

    # Rolling stability
    pred_df = pred_df.sort_index().copy()
    roll_ic = pred_df["y_true"].rolling(rolling_window).corr(pred_df["y_pred"])
    roll_rank = (
        pred_df["y_true"]
        .rolling(rolling_window)
        .corr(pred_df["y_pred"].rank())
    )
    rolling_df = pd.DataFrame(
        {
            "date": pred_df.index,
            "rolling_IC": roll_ic.values,
            "rolling_RankIC": roll_rank.values,
        }
    ).dropna()

    # Regime analysis (bull/bear by trailing return, high/low vol by rolling vol median)
    ret = pred_df["y_true"]
    vol = ret.rolling(rolling_window).std()
    vol_med = float(vol.median(skipna=True))
    regime_rows: list[dict] = []
    regimes = {
        "bull_high_vol": (ret > 0) & (vol >= vol_med),
        "bull_low_vol": (ret > 0) & (vol < vol_med),
        "bear_high_vol": (ret <= 0) & (vol >= vol_med),
        "bear_low_vol": (ret <= 0) & (vol < vol_med),
    }
    for name, mask in regimes.items():
        sub = pred_df.loc[mask].dropna(subset=["y_true", "y_pred"])
        if len(sub) < 20:
            regime_rows.append(
                {"regime": name, "IC": np.nan, "RankIC": np.nan, "n_samples": int(len(sub))}
            )
            continue
        regime_rows.append(
            {
                "regime": name,
                "IC": float(ic(sub["y_true"].values, sub["y_pred"].values)),
                "RankIC": float(rank_ic(sub["y_true"].values, sub["y_pred"].values)),
                "n_samples": int(len(sub)),
            }
        )
    regime_df = pd.DataFrame(regime_rows)

    # Outputs
    out_base = Path("reports/summary/stability")
    out_fig = out_base / "figures"
    out_sum = Path("reports/summary/rolling_regime_summary.md")
    out_base.mkdir(parents=True, exist_ok=True)
    out_fig.mkdir(parents=True, exist_ok=True)
    out_sum.parent.mkdir(parents=True, exist_ok=True)

    rolling_csv = out_base / "rolling_stability.csv"
    regime_csv = out_base / "regime_analysis.csv"
    rolling_df.to_csv(rolling_csv, index=False, encoding="utf-8")
    regime_df.to_csv(regime_csv, index=False, encoding="utf-8")

    plt.figure(figsize=(8, 4))
    plt.plot(pd.to_datetime(rolling_df["date"]), rolling_df["rolling_IC"], label="rolling_IC")
    plt.axhline(0.0, color="gray", linestyle="--", linewidth=1.0)
    plt.title(f"Rolling IC (window={rolling_window})")
    plt.xlabel("date")
    plt.ylabel("IC")
    plt.tight_layout()
    fig_roll = out_fig / "rolling_ic_curve.pdf"
    plt.savefig(fig_roll, format="pdf")
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.bar(regime_df["regime"], regime_df["IC"])
    plt.axhline(0.0, color="gray", linestyle="--", linewidth=1.0)
    plt.xticks(rotation=20, ha="right")
    plt.ylabel("IC")
    plt.title("Regime IC Comparison")
    plt.tight_layout()
    fig_regime = out_fig / "regime_ic_bar.pdf"
    plt.savefig(fig_regime, format="pdf")
    plt.close()

    best_regime = regime_df.dropna(subset=["IC"])
    best_regime_name = (
        best_regime.loc[best_regime["IC"].idxmax(), "regime"]
        if not best_regime.empty else "unknown"
    )
    with open(out_sum, "w", encoding="utf-8") as f:
        f.write("# Rolling Stability + Regime Summary\n\n")
        f.write(f"- config_name: `{exp_cfg.get('experiment_name', 'unknown')}`\n")
        f.write(f"- model_name: `{model_name}`\n")
        f.write(f"- rolling_window: `{rolling_window}`\n")
        f.write(f"- best regime by IC: `{best_regime_name}`\n")
        f.write(f"- rolling rows: `{len(rolling_df)}`\n\n")
        f.write("## Interpretation\n")
        f.write("- Rolling IC varies over time, indicating temporal instability in predictive signal strength.\n")
        f.write("- Regime-level IC differences suggest conditional predictability across volatility/trend states.\n")
        f.write("- Stability diagnostics should be combined with horizon and feature diagnostics before strategy claims.\n")

    click.echo("\n── Rolling Stability + Regime Diagnostics ──")
    click.echo(f"Saved CSV: {rolling_csv}")
    click.echo(f"Saved CSV: {regime_csv}")
    click.echo(f"Saved figure: {fig_roll}")
    click.echo(f"Saved figure: {fig_regime}")
    click.echo(f"Saved markdown: {out_sum}")


# ── backtest ──────────────────────────────────────────────────

@cli.command("backtest")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default=None, type=str)
@click.option(
    "--task",
    default=None,
    type=click.Choice(["regression", "classification"]),
    help="Prediction task. Default resolves from config.",
)
@click.option(
    "--dataset-variant",
    default=None,
    type=click.Choice(
        ["onchain", "ta", "all", "boruta_onchain", "boruta_ta", "boruta_all", "univariate"]
    ),
    help="Dataset variant. Default resolves from config.",
)
def backtest(
    config: str,
    data_config: str,
    model_name: Optional[str],
    task: Optional[str],
    dataset_variant: Optional[str],
):
    """Run backtest on saved predictions and print performance table."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    prefix = _artifact_prefix(exp_cfg)
    symbol = exp_cfg.get("symbol", "BTC-USD")
    strat_cfg = exp_cfg.get("strategy", {})
    cost_list = strat_cfg.get("cost_bps", [5, 10, 20])
    task_name = _resolve_task(task, exp_cfg, data_cfg)
    resolved_model_name = _resolve_selected_model(model_name, exp_cfg)
    variant_name = _resolve_dataset_variant(dataset_variant, exp_cfg)

    pred_path = (
        f"data/features/{prefix}_{resolved_model_name}_"
        f"{task_name}_{variant_name}_preds.parquet"
    )
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
    if task_name == "classification":
        predictions = predictions.astype(float) - 0.5
    signal = make_signal(
        predictions,
        mode=strat_cfg.get("mode", "long_only"),
        top_quantile=float(strat_cfg.get("top_quantile", 0.2)),
        bottom_quantile=float(strat_cfg.get("bottom_quantile", 0.2)),
    )

    sensitivity_df = sensitivity_analysis(price_df, signal, cost_bps_list=cost_list)
    click.echo(
        f"\n── Backtest Sensitivity (symbol={symbol}, model={resolved_model_name}, "
        f"task={task_name}, variant={variant_name}) ──"
    )
    click.echo(sensitivity_df.to_string())

    sensitivity_path = (
        f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_backtest_sensitivity.csv"
    )
    sensitivity_df.reset_index().to_csv(sensitivity_path, index=False, encoding="utf-8")

    # Save equity curve for default cost
    default_bps = float(strat_cfg.get("default_cost_bps", 10))
    result = run_backtest(price_df, signal, cost_bps=default_bps)
    equity = result["equity"]
    equity_path = (
        f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_equity.parquet"
    )
    equity.to_frame("equity").to_parquet(equity_path)

    click.secho(f"\n✓ backtest complete (equity → {equity_path})", fg="green", bold=True)


# ── report ────────────────────────────────────────────────────

@cli.command("report")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--model", "model_name", default=None, type=str)
@click.option(
    "--task",
    default=None,
    type=click.Choice(["regression", "classification"]),
    help="Prediction task. Default resolves from config.",
)
@click.option(
    "--dataset-variant",
    default=None,
    type=click.Choice(
        ["onchain", "ta", "all", "boruta_onchain", "boruta_ta", "boruta_all", "univariate"]
    ),
    help="Dataset variant. Default resolves from config.",
)
def report(
    config: str,
    data_config: str,
    model_name: Optional[str],
    task: Optional[str],
    dataset_variant: Optional[str],
):
    """Generate all figures and write summary HTML report."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    exp_name = exp_cfg["experiment_name"]
    prefix = _artifact_prefix(exp_cfg)
    symbol = exp_cfg.get("symbol", "BTC-USD")
    fig_dir = Path(exp_cfg.get("output", {}).get("figures_dir", "reports/experiments/figures"))
    trd_dir = Path(exp_cfg.get("output", {}).get("trading_dir", "reports/experiments/trading"))
    rpt_dir = Path(
        exp_cfg.get("output", {}).get(
            "report_summaries_dir", "reports/experiments/summaries"
        )
    )
    strat_cfg = exp_cfg.get("strategy", {})
    task_name = _resolve_task(task, exp_cfg, data_cfg)
    resolved_model_name = _resolve_selected_model(model_name, exp_cfg)
    variant_name = _resolve_dataset_variant(dataset_variant, exp_cfg)

    # ── Load predictions ───────────────────────────────────────
    pred_path = (
        f"data/features/{prefix}_{resolved_model_name}_"
        f"{task_name}_{variant_name}_preds.parquet"
    )
    equity_path = (
        f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_equity.parquet"
    )

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
        eq_path  = plot_equity_curves({resolved_model_name: equity}, out_dir=fig_dir,
                                      filename=f"{prefix}_{resolved_model_name}_{task_name}_{variant_name}_equity.pdf")
        dd_path  = plot_drawdown(equity, out_dir=fig_dir,
                                 filename=f"{prefix}_{resolved_model_name}_{task_name}_{variant_name}_drawdown.pdf")
        logger.info(f"Equity → {eq_path}")
        logger.info(f"Drawdown → {dd_path}")

    pa_path = plot_pred_vs_actual(y_true, y_pred, out_dir=fig_dir,
                                  filename=f"{prefix}_{resolved_model_name}_{task_name}_{variant_name}_pred_vs_actual.pdf")
    logger.info(f"Pred vs Actual → {pa_path}")

    # ── Plotly interactive chart ───────────────────────────────
    from src.backtest.strategy import make_signal
    from src.visualization.plotly_trading_chart import make_trading_chart

    signal_scores = y_pred.astype(float) - 0.5 if task_name == "classification" else y_pred
    signal = make_signal(
        signal_scores,
        mode=strat_cfg.get("mode", "long_only"),
        top_quantile=float(strat_cfg.get("top_quantile", 0.2)),
        bottom_quantile=float(strat_cfg.get("bottom_quantile", 0.2)),
    )
    html_path = make_trading_chart(
        price_df=price_df,
        predictions=y_pred,
        signal=signal,
        symbol=symbol,
        model_name=resolved_model_name,
        out_dir=trd_dir,
    )
    logger.info(f"Plotly chart → {html_path}")

    # ── Load metrics ───────────────────────────────────────────
    metrics_path = f"data/features/{prefix}_{resolved_model_name}_{task_name}_{variant_name}_metrics.json"
    metrics = {}
    if Path(metrics_path).exists():
        metrics = _read_json_file(metrics_path)

    # ── Write markdown summary ─────────────────────────────────
    feat_path = f"data/features/{prefix}.parquet"
    n_feat = 0
    if Path(feat_path).exists():
        from src.datasets.build_dataset import get_feature_cols_by_variant
        tmp = pd.read_parquet(feat_path)
        label_col = _resolve_label_col(task_name, exp_cfg, data_cfg)
        n_feat = len(
            get_feature_cols_by_variant(
                tmp,
                label_col=label_col,
                dataset_variant=variant_name,
            )
        )

    rpt_dir.mkdir(parents=True, exist_ok=True)
    summary_path = rpt_dir / f"{prefix}_summary_{resolved_model_name}_{task_name}_{variant_name}.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Crypto Predict — Summary Report\n\n")
        f.write(f"**Experiment**: `{exp_name}`  \n")
        f.write(f"**Symbol**: `{symbol}`  \n")
        f.write(f"**Model**: `{resolved_model_name}`  \n")
        f.write(f"**Task**: `{task_name}`  \n")
        f.write(f"**Dataset Variant**: `{variant_name}`  \n")
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


@cli.command("experiment-summary")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
@click.option("--cost-bps", default=5.0, type=float, show_default=True)
def experiment_summary(config: str, data_config: str, cost_bps: float):
    """Aggregate metrics/backtests into a ranking table for current experiment."""
    exp_cfg = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)
    prefix = _artifact_prefix(exp_cfg)

    out_dir = Path(exp_cfg.get("output", {}).get("summary_dir", "reports/summary"))
    out_dir.mkdir(parents=True, exist_ok=True)
    feature_path = Path(f"data/features/{prefix}.parquet")
    feature_df = pd.read_parquet(feature_path) if feature_path.exists() else None

    model_names = [m.lower() for m in exp_cfg.get("comparison", {}).get("ml_models", [])]
    model_names += [m.lower() for m in exp_cfg.get("comparison", {}).get("dl_models", [])]
    model_names += ["xgboost", "gbm"]
    model_names = sorted(set(model_names), key=len, reverse=True)

    def parse_metrics_name(path: Path) -> tuple[str, str, str] | None:
        stem = path.stem
        base = f"{prefix}_"
        if not stem.startswith(base) or not stem.endswith("_metrics"):
            return None
        body = stem[len(base):-len("_metrics")]
        for model in model_names:
            marker = f"{model}_"
            if body.startswith(marker):
                rest = body[len(marker):]
                for task_name in ("classification", "regression"):
                    task_marker = f"{task_name}_"
                    if rest.startswith(task_marker):
                        variant = rest[len(task_marker):]
                        return model, task_name, variant
        return None

    def selected_feature_count(model: str, task_name: str, variant: str) -> Optional[int]:
        meta_path = Path(f"models_saved/{prefix}_{model}_{task_name}_{variant}_meta.json")
        if meta_path.exists():
            meta = _read_json_file(meta_path)
            if "feature_cols" in meta:
                return len(meta["feature_cols"])
        train_log = Path(f"reports/batch_runs/{model}_{task_name}_{variant}_train.log")
        if train_log.exists():
            text = train_log.read_text(encoding="utf-8", errors="ignore")
            lasso_match = re.findall(r"Lasso refinement kept (\d+)/(\d+) features", text)
            if lasso_match:
                return int(lasso_match[-1][0])
            boruta_match = re.findall(r"Boruta proxy kept (\d+)/(\d+) features", text)
            if boruta_match:
                return int(boruta_match[-1][0])
        if feature_df is not None:
            from src.datasets.build_dataset import get_feature_cols_by_variant
            label_col = _resolve_label_col(task_name, exp_cfg, data_cfg)
            try:
                return len(get_feature_cols_by_variant(feature_df, label_col=label_col, dataset_variant=variant))
            except Exception:
                return None
        return None

    def load_backtest_row(model: str, task_name: str, variant: str) -> dict:
        csv_path = Path(
            f"data/features/{prefix}_{model}_{task_name}_{variant}_backtest_sensitivity.csv"
        )
        if csv_path.exists():
            sdf = pd.read_csv(csv_path)
            row = sdf.loc[np.isclose(sdf["cost_bps"].astype(float), float(cost_bps))]
            if not row.empty:
                return row.iloc[0].to_dict()

        log_path = Path(f"reports/batch_runs/{model}_{task_name}_{variant}_backtest.log")
        if not log_path.exists():
            return {}
        text = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        pattern = re.compile(
            r"^\s*(?P<cost>[-0-9.]+)\s+(?P<cumulative_return>[-0-9.]+)\s+"
            r"(?P<annualised_return>[-0-9.]+)\s+(?P<annualised_volatility>[-0-9.]+)\s+"
            r"(?P<max_drawdown>[-0-9.]+)\s+(?P<sharpe_ratio>[-0-9.]+)\s+"
            r"(?P<turnover>[-0-9.]+)\s+(?P<n_days>\d+)"
        )
        for line in text:
            match = pattern.match(line)
            if match and np.isclose(float(match.group("cost")), float(cost_bps)):
                row = {k: float(v) for k, v in match.groupdict().items() if k != "n_days"}
                row["n_days"] = int(match.group("n_days"))
                row["cost_bps"] = float(match.group("cost"))
                return row
        return {}

    rows: list[dict] = []
    for metrics_path in sorted(Path("data/features").glob(f"{prefix}_*_metrics.json")):
        parsed = parse_metrics_name(metrics_path)
        if not parsed:
            continue
        model, task_name, variant = parsed
        metrics = _read_json_file(metrics_path)
        row = {
            "model": model,
            "task": task_name,
            "variant": variant,
            "selected_feature_count": selected_feature_count(model, task_name, variant),
        }
        row.update(metrics)
        row.update(load_backtest_row(model, task_name, variant))
        rows.append(row)

    if not rows:
        click.secho("No experiment artifacts found for summary.", fg="red")
        sys.exit(1)

    summary_df = pd.DataFrame(rows)
    summary_df["predictive_score"] = np.nan
    summary_df["trading_score"] = np.nan

    for idx, row in summary_df.iterrows():
        model = str(row["model"])
        task_name = str(row["task"])
        if task_name == "classification":
            f1_key = f"{model}_classification_oos_f1"
            if f1_key in summary_df.columns:
                summary_df.at[idx, "predictive_score"] = row.get(f1_key)
        elif task_name == "regression":
            rmse_key = f"{model}_regression_oos_rmse"
            ic_key = f"{model}_regression_oos_ic"
            if rmse_key in summary_df.columns:
                summary_df.at[idx, "rmse"] = row.get(rmse_key)
                if pd.notna(row.get(rmse_key)):
                    summary_df.at[idx, "predictive_score"] = -float(row.get(rmse_key))
            if ic_key in summary_df.columns:
                summary_df.at[idx, "ic"] = row.get(ic_key)

    if "cumulative_return" in summary_df.columns:
        summary_df["trading_score"] = summary_df["cumulative_return"]

    summary_df["predictive_rank"] = (
        summary_df.groupby("task")["predictive_score"].rank(ascending=False, method="dense")
    )
    summary_df["trading_rank"] = (
        summary_df.groupby("task")["trading_score"].rank(ascending=False, method="dense")
    )

    sort_df = summary_df.sort_values(
        ["task", "trading_rank", "predictive_rank", "model", "variant"]
    ).reset_index(drop=True)

    out_csv = out_dir / f"{prefix}_experiment_summary.csv"
    out_md = out_dir / f"{prefix}_experiment_summary.md"
    selection_csv = out_dir / f"{prefix}_selection_summary.csv"
    selection_md = out_dir / f"{prefix}_selection_summary.md"
    sort_df.to_csv(out_csv, index=False, encoding="utf-8")

    def _pick_row(task_name: str, purpose: str) -> Optional[pd.Series]:
        task_df = sort_df[sort_df["task"] == task_name].copy()
        if task_df.empty:
            return None
        if purpose == "experiment":
            if task_name == "classification":
                metric_col = "predictive_score"
                ascending = False
                tie_cols = ["trading_score"]
                tie_ascending = [False]
            else:
                metric_col = "rmse"
                ascending = True
                tie_cols = ["ic", "trading_score"]
                tie_ascending = [False, False]
        else:
            metric_col = "trading_score"
            ascending = False
            tie_cols = ["sharpe_ratio", "max_drawdown"]
            tie_ascending = [False, False]
        available_sort_cols = [metric_col] + [c for c in tie_cols if c in task_df.columns]
        available_ascending = [ascending] + tie_ascending[: len(available_sort_cols) - 1]
        task_df = task_df.sort_values(available_sort_cols, ascending=available_ascending, na_position="last")
        return task_df.iloc[0]

    selection_rows: list[dict] = []
    for task_name in ("classification", "regression"):
        experiment_row = _pick_row(task_name, "experiment")
        if experiment_row is not None:
            selection_rows.append(
                {
                    "selection_type": f"{task_name}_experiment_winner",
                    "task": task_name,
                    "model": experiment_row["model"],
                    "variant": experiment_row["variant"],
                    "selected_feature_count": experiment_row.get("selected_feature_count"),
                    "predictive_score": experiment_row.get("predictive_score"),
                    "trading_score": experiment_row.get("trading_score"),
                    "cumulative_return": experiment_row.get("cumulative_return"),
                    "sharpe_ratio": experiment_row.get("sharpe_ratio"),
                    "max_drawdown": experiment_row.get("max_drawdown"),
                    "rule": "classification: highest F1; regression: lowest RMSE, tie-break by IC then trading score",
                }
            )
        return_row = _pick_row(task_name, "return")
        if return_row is not None:
            selection_rows.append(
                {
                    "selection_type": f"{task_name}_return_winner",
                    "task": task_name,
                    "model": return_row["model"],
                    "variant": return_row["variant"],
                    "selected_feature_count": return_row.get("selected_feature_count"),
                    "predictive_score": return_row.get("predictive_score"),
                    "trading_score": return_row.get("trading_score"),
                    "cumulative_return": return_row.get("cumulative_return"),
                    "sharpe_ratio": return_row.get("sharpe_ratio"),
                    "max_drawdown": return_row.get("max_drawdown"),
                    "rule": "highest cumulative return, tie-break by Sharpe then drawdown",
                }
            )

    regression_return_row = _pick_row("regression", "return")
    if regression_return_row is not None:
        selection_rows.append(
            {
                "selection_type": "final_return_model",
                "task": "regression",
                "model": regression_return_row["model"],
                "variant": regression_return_row["variant"],
                "selected_feature_count": regression_return_row.get("selected_feature_count"),
                "predictive_score": regression_return_row.get("predictive_score"),
                "trading_score": regression_return_row.get("trading_score"),
                "cumulative_return": regression_return_row.get("cumulative_return"),
                "sharpe_ratio": regression_return_row.get("sharpe_ratio"),
                "max_drawdown": regression_return_row.get("max_drawdown"),
                "rule": "final model for return prediction: regression return winner",
            }
        )

    selection_df = pd.DataFrame(selection_rows)
    selection_df.to_csv(selection_csv, index=False, encoding="utf-8")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Experiment Summary\n\n")
        f.write(f"- config_name: `{exp_cfg.get('experiment_name', 'unknown')}`\n")
        f.write(f"- artifact_prefix: `{prefix}`\n")
        f.write(f"- summary_cost_bps: `{cost_bps}`\n\n")
        for task_name in ("classification", "regression"):
            task_df = sort_df[sort_df["task"] == task_name].copy()
            if task_df.empty:
                continue
            f.write(f"## {task_name.title()}\n\n")
            cols = ["model", "variant", "selected_feature_count", "predictive_rank", "trading_rank"]
            if task_name == "classification":
                metric_cols = [
                    c for c in task_df.columns
                    if c.endswith("_classification_oos_accuracy")
                    or c.endswith("_classification_oos_precision")
                    or c.endswith("_classification_oos_recall")
                    or c.endswith("_classification_oos_f1")
                ]
            else:
                metric_cols = [
                    c for c in task_df.columns
                    if c.endswith("_regression_oos_mae")
                    or c.endswith("_regression_oos_rmse")
                    or c.endswith("_regression_oos_ic")
                    or c.endswith("_regression_oos_rank_ic")
                ]
            cols += [c for c in metric_cols if c in task_df.columns]
            cols += [c for c in ["cumulative_return", "annualised_return", "sharpe_ratio", "max_drawdown"] if c in task_df.columns]
            f.write(_dataframe_to_markdown(task_df[cols]))
            f.write("\n\n")

    with open(selection_md, "w", encoding="utf-8") as f:
        f.write("# Selection Summary\n\n")
        f.write(f"- config_name: `{exp_cfg.get('experiment_name', 'unknown')}`\n")
        f.write(f"- artifact_prefix: `{prefix}`\n")
        f.write(f"- summary_cost_bps: `{cost_bps}`\n\n")
        f.write("## Rules\n\n")
        f.write("- Classification experiment winner: highest F1.\n")
        f.write("- Regression experiment winner: lowest RMSE, tie-break by IC then trading score.\n")
        f.write("- Return winner: highest cumulative return, tie-break by Sharpe then drawdown.\n")
        f.write("- Final return model: regression return winner.\n\n")
        if not selection_df.empty:
            cols = [
                "selection_type",
                "task",
                "model",
                "variant",
                "selected_feature_count",
                "predictive_score",
                "trading_score",
                "cumulative_return",
                "sharpe_ratio",
                "max_drawdown",
                "rule",
            ]
            f.write(_dataframe_to_markdown(selection_df[cols]))
            f.write("\n")

    click.echo("\n── Experiment Summary ──")
    click.echo(sort_df.to_string(index=False))
    click.secho(f"\n✓ experiment summary → {out_csv}", fg="green", bold=True)
    click.echo(f"  markdown : {out_md}")
    click.echo(f"  selection: {selection_csv}")
    click.echo(f"  sel_md   : {selection_md}")


# ── validate ─────────────────────────────────────────────────

@cli.command("validate")
@click.option("--config", default="configs/experiment.yaml")
@click.option("--data-config", default="configs/data.yaml")
def validate(config: str, data_config: str):
    """Run leakage guard checks. Exits with code 1 if violations found."""
    exp_cfg  = _load_exp_cfg(config)
    data_cfg = _load_data_cfg(data_config)

    feat_path = f"data/features/{_artifact_prefix(exp_cfg)}.parquet"

    if not Path(feat_path).exists():
        click.secho("Feature file not found, building …", fg="yellow")
        from src.datasets.build_dataset import build_dataset
        build_dataset(**_build_dataset_kwargs(exp_cfg, data_cfg, output_path=feat_path))

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
