# Project Plan

## 1. Goal
Build a unified graduation-research pipeline to evaluate whether on-chain factors
improve crypto prediction quality and trading performance.

The project compares:
- Task: direction classification vs magnitude regression
- Model type: ML vs DL
- Data variant: 7 dataset variants

## 2. Scope
- Keep one master configuration (`configs/experiment.yaml`).
- Expand data coverage and quality, guided by the paper methodology.
- Do not run old iteration-based workflows.

## 3. Research Matrix
- Tasks:
  - Classification (up/down)
  - Regression (future return magnitude)
- Models:
  - ML: SVM, RF, GBM, XGBoost, LightGBM
  - DL: LSTM, CNN-LSTM, CNN-GRU, TCN, LSTNet
- Dataset variants:
  - onchain
  - ta
  - all
  - boruta_onchain
  - boruta_ta
  - boruta_all
  - univariate

## 4. Data and Leakage Principles
- Chronological split only, no shuffle.
- Standardization after split, fit scaler only on train.
- Feature selection only on train split.
- For DL use windowed tensors (`timesteps=5`) and strict label alignment.
- On-chain fill policy: forward-fill only; backward-fill forbidden.

## 5. Evaluation and Selection
- Classification metrics: Accuracy, Precision, Recall, F1.
- Regression metrics: RMSE, R2, MAE, directional accuracy.
- Backtest metrics: annual return, max drawdown, sharpe, turnover.
- Model selection rule: combine predictive metrics with backtest, not RMSE alone.

## 6. Output Contract
- All run artifacts go to `reports/`.
- All methodology and writing notes stay in `docs/`.
- Config entry points:
  - `configs/data.yaml`
  - `configs/experiment.yaml`

## 7. Immediate Engineering Tasks
1. Connect `tasks` and `datasets.variants` in CLI training path.
2. Add classification evaluator and output table for both tasks.
3. Add DL data window builder and model adapters.
4. Export unified result registry keyed by:
   - date_range
   - task
   - model
   - dataset_variant
   - metric set
