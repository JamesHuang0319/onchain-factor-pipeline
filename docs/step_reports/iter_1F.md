# Iter-1F Consolidated Report (Step-1/2/3)

## Objective
Build a full V1 diagnostics framework across:
- Step-1: model-level horizon sweep
- Step-2: feature × horizon IC matrix
- Step-3: rolling stability + regime analysis

## Scope lock reminder (V1 sources only until Iter-1D done)
- Allowed: `yfinance`, `Blockchain.com`, `macro dummy`
- Prohibited: `FRED`, `Glassnode`, `CoinMetrics`, `Deribit`

## Step-1 (Horizon Sweep)
### Branch name
`iter-1F-horizon-sweep`

### Files modified (list)
- `src/cli.py`
- `configs/experiment_price_onchain.yaml`

### Data/metrics added or changed
- Horizons evaluated:
  - `1,2,3,5,7,10,14,21,30,45,60,90,120,180`
- Summary output:
  - `reports/01_model_level/horizon_sweep_summary.csv`
- Figures:
  - `reports/01_model_level/figures/horizon_ic_curve.pdf`
  - `reports/01_model_level/figures/horizon_oos_r2_curve.pdf`
- Executive summary:
  - `reports/00_summary/horizon_sweep_summary.md`
- Best horizons (from CSV):
  - Best by `IC_mean`: `h=180` (`0.1764746090061189`)
  - Best by `RankIC_mean`: `h=180` (`0.1931867565578665`)
  - Best by `OOS_R2_mean`: `h=2` (`-0.0114784123742991`)

### Validation commands + results
- `python -m src.cli horizon-sweep --config configs/experiment_price_onchain.yaml --model lgbm` : PASS
- `python -m src.cli build-features --config configs/experiment_price_onchain.yaml` : PASS
- `python -m src.cli validate --config configs/experiment_price_onchain.yaml` : PASS
- `pytest tests/test_no_leakage.py -v` : PASS (7 passed)

### Known limitations / follow-ups
- Some long-horizon folds may trigger constant-input correlation warnings; no leakage assertion failure observed.

## Step-2 (Feature × Horizon IC Matrix)
### Branch name
`iter-1F-feature-horizon-matrix`

### Files modified (list)
- `src/cli.py`

### Data/metrics added or changed
- Matrix output:
  - `reports/02_feature_level/feature_horizon_ic_matrix.csv`
- Figure:
  - `reports/02_feature_level/figures/feature_horizon_ic_heatmap.pdf`
- Executive summary:
  - `reports/00_summary/feature_horizon_matrix_summary.md`
- Matrix stats:
  - Rows: `1148`
  - Features: `82`
  - Horizons: `14`
  - Best by `IC_mean`: `williams_r_30d @ h=180` (`0.2484577177710028`)
  - Best by `RankIC_mean`: `williams_r_30d @ h=180` (`0.260345369920944`)

### Validation commands + results
- `python -m src.cli feature-horizon-matrix --config configs/experiment_price_onchain.yaml` : PASS
- `python -m src.cli build-features --config configs/experiment_price_onchain.yaml` : PASS
- `python -m src.cli validate --config configs/experiment_price_onchain.yaml` : PASS
- `pytest tests/test_no_leakage.py -v` : PASS (7 passed)

### Known limitations / follow-ups
- Matrix is feature-correlation diagnostic, not causal attribution; should be interpreted jointly with Step-1 and Step-3 stability outputs.

## Step-3 (Rolling Stability + Regime)
### Branch name
`iter-1F-rolling-regime-stability`

### Files modified (list)
- `src/cli.py`

### Data/metrics added or changed
- Rolling stability output:
  - `reports/03_stability/rolling_stability.csv`
- Regime output:
  - `reports/03_stability/regime_analysis.csv`
- Figures:
  - `reports/03_stability/figures/rolling_ic_curve.pdf`
  - `reports/03_stability/figures/regime_ic_bar.pdf`
- Executive summary:
  - `reports/00_summary/rolling_regime_summary.md`
- Key stats:
  - Rolling rows: `2927`
  - Rolling IC mean: `-0.0068895527940979395`
  - Rolling RankIC mean: `-0.008608810006281846`
  - Best regime by IC: `bull_low_vol` (`0.0461113493800828`)

### Validation commands + results
- `python -m src.cli stability-regime --config configs/experiment_price_onchain.yaml --model lgbm` : PASS
- `python -m src.cli build-features --config configs/experiment_price_onchain.yaml` : PASS
- `python -m src.cli validate --config configs/experiment_price_onchain.yaml` : PASS
- `pytest tests/test_no_leakage.py -v` : PASS (7 passed)

### Known limitations / follow-ups
- Regime split is rule-based (`bull/bear × high/low vol`); regime taxonomy can be refined in later iterations without changing V1 source scope.
