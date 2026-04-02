# Data Foundation Plan

## Objective
Build a robust data baseline before model comparison:
- stable date alignment
- no leakage
- clear quality gates
- reproducible data artifacts

## Scope
1. Data ingestion:
- price (BTC-USD daily)
- on-chain metrics (primary blockchain source, expandable providers)

2. Feature base:
- price factors
- on-chain factors
- optional macro block

3. Labels:
- regression: `log_ret_h`
- classification: `direction_h`

## Quality Gates (from `configs/data.yaml`)
- minimum total rows
- max feature missing ratio
- class balance range
- train/test minimum row thresholds

## Data Audit Workflow
1. Run:
```bash
python -m src.cli data-audit --config configs/experiment.yaml --dataset-variant all
```
2. Check outputs under:
- `reports/00_summary/data_audit/<experiment>/<dataset_variant>/summary.csv`
- `missing_top20.csv`
- `split_info.csv`
- `class_balance.csv`
3. If gates fail, fix data before any model training.

## Required Daily Discipline
1. `download-data`
2. `build-features`
3. `data-audit`
4. `validate`
5. then `train/backtest/report`

## Notes
- `docs/` stores methodology and planning text only.
- `reports/` stores generated experiment artifacts only.

## Glassnode Expansion
To enable the paper-scale metric expansion:
1. Set API key env:
```bash
set GLASSNODE_API_KEY=your_key_here
```
2. In `configs/data.yaml`:
- set `onchain.providers.glassnode.enabled: true`
- keep/adjust `onchain.providers.glassnode.metrics`
3. Run:
```bash
python -m src.cli download-data --config configs/experiment.yaml --data-config configs/data.yaml --force
python -m src.cli build-features --config configs/experiment.yaml --data-config configs/data.yaml --force
python -m src.cli data-audit --config configs/experiment.yaml --dataset-variant onchain
```
