# Thesis Notes

## 1. Thesis Positioning
Graduation topic focus:
- On-chain-based crypto return prediction
- Statistical validity + trading validity

## 2. Core Claims to Validate
1. On-chain features provide incremental value beyond price/TA-only baselines.
2. Direction task may be more robust for trading than magnitude task.
3. Model effectiveness depends on dataset variant and regime.

## 3. Result Writing Template
- Data scope:
  - assets
  - date range
  - feature family
- Experiment setup:
  - split method
  - task type
  - model list
  - dataset variants
- Metrics:
  - predictive
  - backtest
- Interpretation:
  - what improved
  - where it failed
  - why it matters

## 4. Figure and Table Mapping
- Predictive comparison:
  - task x model x dataset tables
- Stability diagnostics:
  - rolling IC
  - regime comparison
- Economic diagnostics:
  - equity curve
  - drawdown
  - fee sensitivity

## 5. Risks to Discuss
- Regime dependency
- Overfitting under feature expansion
- Data availability and provider bias
- Backtest assumption simplification

## 6. Final Conclusion Style
- Do not conclude by one metric only.
- Report tradeoff:
  - accuracy vs stability
  - fit vs profitability
  - complexity vs reproducibility
