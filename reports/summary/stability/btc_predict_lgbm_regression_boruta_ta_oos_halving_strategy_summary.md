# Halving Period and Strategy Study

- model: `lgbm`
- task: `regression`
- dataset_variant: `boruta_ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | regression | boruta_ta | long_only_sign | 5.000000 | 0.797068 | 0.797068 | 0.000000 | 1.119296 | 0.067219 | 0.143970 | -0.744742 | 0.110584 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | regression | boruta_ta | quantile_long_only_0.20 | 5.000000 | 0.206111 | 0.206111 | 0.000000 | 0.849484 | 0.054705 | 0.218161 | -0.644912 | 0.093972 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
