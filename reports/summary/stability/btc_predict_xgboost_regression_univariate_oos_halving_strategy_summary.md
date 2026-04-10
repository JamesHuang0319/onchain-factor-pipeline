# Halving Period and Strategy Study

- model: `xgboost`
- task: `regression`
- dataset_variant: `univariate`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | univariate | long_only_band_0.0025 | 5.000000 | 0.281173 | 0.281173 | 0.000000 | -0.173629 | -0.016383 | -0.060344 | -0.598281 | 0.059801 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | univariate | long_only_sign | 5.000000 | 0.528082 | 0.528082 | 0.000000 | -0.227875 | -0.022151 | -0.056433 | -0.700098 | 0.063598 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
