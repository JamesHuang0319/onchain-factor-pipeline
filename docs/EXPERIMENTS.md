# Experiments

## 1. Unified Experiment Driver
All runs are controlled by:
- `configs/experiment.yaml`
- `configs/data.yaml`

No old iteration config should be used.

Model decision policy:
- You choose model manually via `--model`.
- Optional default can be set in `configs/experiment.yaml -> decision.selected_model`.

## 2. Experiment Axes
- Task axis:
  - classification
  - regression
- Model axis:
  - ML models
  - DL models
- Dataset axis:
  - onchain
  - ta
  - all
  - boruta_onchain
  - boruta_ta
  - boruta_all
  - univariate

## 3. Minimal Run Order
1. `download-data`
2. `build-features`
3. `data-audit`
4. `validate`
5. `train`
6. `backtest`
7. `report`

## 4. Output Location Standard
- All generated artifacts must go to `reports/`:
  - `reports/00_summary`
  - `reports/01_model_level`
  - `reports/02_feature_level`
  - `reports/03_stability`
  - `reports/figures`
  - `reports/trading`

## 5. Result Table Contract
Every experiment output should be traceable by:
- run_id
- date range
- task
- model
- dataset_variant
- split setup
- metrics
- backtest settings

## 6. Acceptance Checklist
- Leakage test passed
- Config snapshot recorded
- Metrics exported
- Backtest exported
- Summary generated
- Run reproducible from the same config
