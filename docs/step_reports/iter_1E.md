# Iter-1E Step Report

## Objective
Run horizon sensitivity study to test whether predictive power depends on forecast horizon while keeping features, model family, walk-forward logic, and data sources fixed.

## Scope lock reminder (V1 sources only until Iter-1D done)
- Allowed: `yfinance`, `Blockchain.com`, `macro dummy`
- Prohibited: `FRED`, `Glassnode`, `CoinMetrics`, `Deribit`

## Branch name
`iter-1E-horizon-sweep`

## Files modified (list)
- `src/datasets/build_dataset.py`
- `configs/experiment_price_onchain.yaml`
- `configs/experiment_price_only.yaml`

## Data/metrics added or changed (list)
- Label horizon is now configurable via `label_horizon_days` (default `7`).
- Label column uses configurable forward horizon and is stored as `log_ret_h`.
- Horizon sweep artifacts generated:
  - `reports/horizon_sweep_summary.csv`
  - `reports/horizon_ic_curve.pdf`
- Horizons evaluated: `1, 3, 7, 14, 30`
- Summary table (from `reports/horizon_sweep_summary.csv`):
  - `h=1`: IC_mean `-0.0283948830`, direction_acc_mean `0.4954769450`, negative_IC_ratio `0.6470588235`, n_folds `17`
  - `h=3`: IC_mean `-0.0689801303`, direction_acc_mean `0.5009184039`, negative_IC_ratio `0.7058823529`, n_folds `17`
  - `h=7`: IC_mean `-0.0145049036`, direction_acc_mean `0.5175399271`, negative_IC_ratio `0.5882352941`, n_folds `17`
  - `h=14`: IC_mean `-0.0644358263`, direction_acc_mean `0.5319677141`, negative_IC_ratio `0.5294117647`, n_folds `17`
  - `h=30`: IC_mean `0.1095585942`, direction_acc_mean `0.5201709771`, negative_IC_ratio `0.1764705882`, n_folds `17`

## Validation commands + results (copy commands; PASS/FAIL)
- `python -m src.cli build-features --config configs/experiment_price_onchain.yaml` : PASS
- `python -m src.cli validate --config configs/experiment_price_onchain.yaml` : PASS
- `pytest tests/test_no_leakage.py -v` : PASS (7 passed)

## Known limitations / follow-ups
- `h=30` improves IC metrics but has the worst mean OOS_R2 in this run, indicating horizon-dependent trade-offs.
- Label column rename to `log_ret_h` may require downstream consumers to avoid hardcoded old target names.
