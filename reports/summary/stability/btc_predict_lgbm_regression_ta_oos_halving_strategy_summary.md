# Halving Period and Strategy Study

- model: `lgbm`
- task: `regression`
- dataset_variant: `ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | regression | ta | quantile_long_only_0.20 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 5.308070 | 0.172962 | 0.755212 | -0.277820 | 0.118178 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | regression | ta | quantile_long_only_0.20 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 5.308070 | 0.172962 | 0.755212 | -0.277820 | 0.118178 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
