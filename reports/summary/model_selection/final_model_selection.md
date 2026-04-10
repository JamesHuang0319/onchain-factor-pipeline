# Final Model Selection

This directory now keeps only current, citation-ready selection artifacts.
Older auto-generated selection outputs are preserved in [`legacy/`](legacy).

## Selection Basis

- Source scope: `OOS` results only
- Trading layer: fixed strategy search space from `halving-strategy-study`
- Core feature line: `boruta_onchain`
- Effective trading start for retained models: `2018-03-17`

## Recommended Models

| Role | Model | Task | Variant | Best Return | Return Strategy | Best Sharpe | Sharpe Strategy | Notes |
| --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| ML classification primary | `rf` | `classification` | `boruta_onchain` | 40.3464 | `sign_band_0.005` | 1.0450 | `quantile_long_only_0.05` | Main classification baseline; strongest robustness story. |
| ML classification return | `xgboost` | `classification` | `boruta_onchain` | 42.4078 | `sign_band_0.01` | 0.8191 | `long_only_band_0.01` | Higher return upside than RF, weaker Sharpe. |
| ML regression primary | `svm` | `regression` | `boruta_onchain` | 50.6960 | `full_exposure_sign` | 0.9221 | `quantile_long_only_0.20` | Strongest traditional regression model after strategy search. |
| ML regression robust | `rf` | `regression` | `boruta_onchain` | 12.3670 | `sign_band_0.0025` | 0.8797 | `quantile_long_only_0.20` | More conservative regression baseline with better risk-adjusted profile than its return winner. |
| DL regression primary | `tcn` | `regression` | `boruta_onchain` | 89.7209 | `sign_band_0.0025` | 1.0465 | `sign_band_0.0025` | Highest OOS return ceiling; keep explicit note that retraining sensitivity is non-trivial. |
| DL classification primary | `tcn` | `classification` | `boruta_onchain` | 7.1729 | `long_only_band_0.01` | 0.9630 | `quantile_long_only_0.10` | Best DL classification reference; Sharpe-oriented mapping is more convincing than its raw return winner. |
| DL regression support | `lstm` | `regression` | `boruta_onchain` | 22.9704 | `sign_band_0.0025` | 0.7579 | `quantile_long_only_0.20` | Secondary DL regression model with lower upside than TCN but easier narrative support. |

## How To Read This Folder

- `final_model_selection.csv`
  - Current final shortlist used for thesis writing and presentation.
- `ml_dl_oos_unified_summary.csv`
  - Cross-model OOS comparison table used as an input table.
- `ml_dl_oos_unified_summary_focus.csv`
  - Focused comparison subset used during model triage.
- `dl_unified_run_summary.csv`
  - DL-only support table from the unified run.
- `legacy/`
  - Older auto-generated selection summaries kept only for traceability.

## Practical Thesis Use

- Classification main text:
  - `rf`, `xgboost`
- Regression main text:
  - `svm`, `tcn`
- DL supplement:
  - `lstm`

Do not use the legacy auto-generated `selection_summary` files as current conclusions.
