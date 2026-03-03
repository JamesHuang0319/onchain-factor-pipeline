# Iter-1C Step Report

## Objective
Run walk-forward incremental evaluation for price-only vs price+onchain and export fold-level metrics to `reports/ic_table.csv`.

## Scope lock reminder (V1 sources only until Iter-1D done)
- Allowed: `yfinance`, `Blockchain.com`, `macro dummy`
- Prohibited: `FRED`, `Glassnode`, `CoinMetrics`, `Deribit`

## Branch name
`iter-1C-ic-eval`

## Files modified (list)
- `src/evaluation/metrics.py`
- `src/evaluation/walk_forward.py`
- `src/cli.py`

## Data/metrics added or changed (list; include reports/ic_table.csv details for 1C)
- Added fold-level OOS metric support in evaluation layer (IC, RankIC, OOS_R2, MAE, MSE, n_samples).
- Added/updated `reports/ic_table.csv`.
- Current `reports/ic_table.csv` details:
  - row count: `34`
  - columns:
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
  - configs present: `iter0_price_only`, `iter1_price_onchain`
  - models present: `lgbm`

## Validation commands + results (copy commands; PASS/FAIL)
- `python -m src.cli train --config configs/experiment_price_only.yaml --model lgbm` : PASS
- `python -m src.cli train --config configs/experiment_price_onchain.yaml --model lgbm` : PASS
- `pytest tests/test_no_leakage.py -v` : PASS (7 passed)

## Known limitations / follow-ups
- Fold-level IC values are mostly negative in current setup; root-cause diagnostics moved to Iter-1D outputs.
- Iter-1C report artifact generation timestamp from git history/log files is unknown (not recorded) in this file.
