# Methodology

## 1. Problem Definition
The project predicts next-period BTC behavior from market and blockchain signals:
- Direction task: predict up/down movement
- Magnitude task: predict future log return

## 2. Data Blocks
- Price block: OHLCV-based features
- On-chain block: blockchain activity and network-state features
- TA block: technical indicators

The master time range is configured in `configs/data.yaml`.

## 3. Labels
- Regression label:
  - `log_ret_h = log(close[t+h] / close[t])`
- Classification label:
  - `direction_h = 1 if log_ret_h > 0 else 0`

Default horizon is controlled by:
- `configs/data.yaml -> prediction.horizon`
- `configs/experiment.yaml -> label_horizon_days`

## 4. Preprocessing Rules
- Merge all feature blocks on the price calendar.
- Handle missing values according to config policy.
- Keep chronological ordering.
- Split by time first, then scale.
- No global fit before split.

## 5. Leakage Guards
- No feature can use information after timestamp `t`.
- Rolling indicators must be backward-looking.
- On-chain data can only be forward-filled.
- Tests in `tests/test_no_leakage.py` must pass before any formal run.

## 6. Feature Selection
- Boruta is used on selected variants:
  - boruta_onchain
  - boruta_ta
  - boruta_all
- Boruta is fit on train split only, then applied to validation/test.

## 7. Model Inputs
- ML input shape:
  - `(samples, features)`
- DL input shape:
  - `(samples, timesteps, features)`
- Current default window:
  - `timesteps = 5`

## 8. Evaluation
- Classification:
  - Accuracy, Precision, Recall, F1
- Regression:
  - RMSE, R2, MAE
- Additional:
  - directional accuracy for regression outputs

## 9. Backtest Mapping
- Prediction up -> long
- Prediction down -> short
- Include transaction cost and tax settings from config.
- Final selection uses both predictive and economic performance.
