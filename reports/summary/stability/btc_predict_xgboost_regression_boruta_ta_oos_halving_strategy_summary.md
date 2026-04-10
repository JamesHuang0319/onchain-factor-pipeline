# Halving Period and Strategy Study

- model: `xgboost`
- task: `regression`
- dataset_variant: `boruta_ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | boruta_ta | long_only_band_0.0025 | 5.000000 | 0.267220 | 0.267220 | 0.000000 | 1.663018 | 0.088540 | 0.327328 | -0.521200 | 0.102515 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | boruta_ta | quantile_long_only_0.05 | 5.000000 | 0.050159 | 0.050159 | 0.000000 | 1.224543 | 0.071708 | 0.475305 | -0.258370 | 0.031324 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
