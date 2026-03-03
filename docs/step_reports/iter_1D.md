# Iter-1D Step Report

## Objective
Add IC diagnostics, alignment sanity checks, and static research-style visualization to investigate negative IC behavior without changing data/model/feature logic.

## Scope lock reminder (V1 sources only until Iter-1D done)
- Allowed: `yfinance`, `Blockchain.com`, `macro dummy`
- Prohibited: `FRED`, `Glassnode`, `CoinMetrics`, `Deribit`

## Branch name
`iter-1D-ic-diagnostics`

## Files modified (list)
- `src/evaluation/walk_forward.py`
- `src/evaluation/ic_diagnostics.py` (new)
- `src/cli.py`

## Data/metrics added or changed (list; include diagnostics artifacts for 1D if applicable)
- Added/updated `reports/ic_diagnostics.csv` with columns:
  - `config_name`
  - `model_name`
  - `fold_id`
  - `start_date`
  - `end_date`
  - `IC`
  - `RankIC`
  - `OOS_R2`
  - `MAE`
  - `MSE`
  - `n_samples`
  - `ic_negative`
- Current `reports/ic_diagnostics.csv` row count: `34`
- Generated diagnostic PDFs:
  - `reports/ic_hist_price_only.pdf`
  - `reports/ic_hist_price_onchain.pdf`
  - `reports/ic_box_compare.pdf`
  - `reports/oos_r2_bar_compare.pdf`
- Alignment sanity diagnostic output (CLI): sampled test dates with `pred`, `label`, `close_t`, `close_t+7`, `manual_log_return`.
  - current result: alignment check passed (`|label - manual_log_return| < 1e-10`)

## Validation commands + results (copy commands; PASS/FAIL)
- `python -m src.cli train --config configs/experiment_price_only.yaml --model lgbm` : PASS
- `python -m src.cli train --config configs/experiment_price_onchain.yaml --model lgbm` : PASS
- `pytest tests/test_no_leakage.py -v` : PASS (7 passed)

## Known limitations / follow-ups
- Negative IC remains frequent (`ic_negative_ratio` currently around `0.588235` for both configs) and requires further factor/strategy-level investigation in future iterations.
- Historical first-run diagnostics values before latest rerun are unknown (not recorded) where not present in versioned artifacts.
