# Iter-1B Step Report

## Objective
Build derived on-chain factors from the 9 Blockchain metrics and keep dataset assembly anti-leakage safe (price index backbone, forward-fill only, no backward fill).

## Scope lock reminder (V1 sources only until Iter-1D done)
- Allowed: `yfinance`, `Blockchain.com`, `macro dummy`
- Prohibited: `FRED`, `Glassnode`, `CoinMetrics`, `Deribit`

## Branch name
`iter-1B-onchain-factors`

## Files modified (list)
- `src/features/onchain_factors.py`
- `src/etl/cleaner.py`
- `docs/step_reports/iter_1B.md`

## Data/metrics added or changed (list, row counts, missing summary if relevant)
- Added 46 new on-chain derived features (safe transforms only: log1p, pct_change, rolling mean deviation, rolling zscore).
- Total feature count for Iter-1 onchain dataset: 82 (`get_feature_cols` result).
- On-chain feature NaN summary (top):
  - 14 NaNs: all `*_z30` columns (rolling warm-up)
  - 7 NaNs: all `*_pct_7d` columns and `hr_diff_ratio_pct_7d` / `tx_per_addr_pct_7d` (lag warm-up)
- No backward fill introduced.

## Validation commands + results (copy the commands and state PASS/FAIL)
- `python -m src.cli build-features --config configs/experiment_price_onchain.yaml` : PASS
- `python -m src.cli validate --config configs/experiment_price_onchain.yaml` : PASS
- `pytest tests/test_no_leakage.py -v` : PASS (7 passed)

## Known limitations / follow-ups
- `src/cli.py` remains modified in workspace from prior UTF-8 stability patch and is intentionally excluded from Iter-1B commit scope.
