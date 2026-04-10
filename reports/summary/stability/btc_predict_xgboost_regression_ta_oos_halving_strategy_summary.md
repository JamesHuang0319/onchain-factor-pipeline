# Halving Period and Strategy Study

- model: `xgboost`
- task: `regression`
- dataset_variant: `ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | ta | long_only_sign | 5.000000 | 0.410279 | 0.410279 | 0.000000 | 7.909501 | 0.208572 | 0.644431 | -0.459458 | 0.139535 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | ta | long_only_sign | 5.000000 | 0.410279 | 0.410279 | 0.000000 | 7.909501 | 0.208572 | 0.644431 | -0.459458 | 0.139535 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
