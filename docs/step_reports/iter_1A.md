# Iter-1A Step Report

## Objective
Extend Blockchain.com on-chain ingestion within V1 locked sources by adding new charts slugs and keeping existing cache/retry behavior unchanged.

## Scope lock reminder (V1 sources only until Iter-1D done)
- Allowed: `yfinance`, `Blockchain.com`, `macro dummy`
- Prohibited: `FRED`, `Glassnode`, `CoinMetrics`, `Deribit`

## Branch name
`iter-1A-blockchain-ingest`

## Files modified (list)
- `src/ingest/onchain.py`
- `configs/data.yaml`

## Data/metrics added or changed (list, row counts, missing summary if relevant)
- Added metrics:
  - `transaction-fees`
  - `estimated-transaction-volume`
  - `mempool-size`
  - `miners-revenue`
  - `cost-per-transaction`
- Current metric file stats (rows, missing):
  - `n-transactions.csv`: 6251, 0
  - `n-unique-addresses.csv`: 6240, 0
  - `transaction-fees.csv`: 6251, 0
  - `estimated-transaction-volume.csv`: 5644, 0
  - `mempool-size.csv`: 3550, 0
  - `miners-revenue.csv`: 6254, 0
  - `cost-per-transaction.csv`: 6254, 0
  - `hash-rate.csv`: 6265, 0
  - `difficulty.csv`: 6265, 0

## Validation commands + results (copy the commands and state PASS/FAIL)
- `python -m src.cli download-data --config configs/experiment_price_onchain.yaml` : PASS
- `pytest tests/test_no_leakage.py -v` : FAIL (`TestOnChainAlignment::test_ffill_direction`)

## Known limitations / follow-ups
- Leakage test suite currently has one failing test (`test_ffill_direction`) that must be addressed in a separate scoped step.
