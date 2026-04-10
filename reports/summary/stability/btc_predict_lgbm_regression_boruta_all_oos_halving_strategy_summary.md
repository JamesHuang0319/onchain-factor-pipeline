# Halving Period and Strategy Study

- model: `lgbm`
- task: `regression`
- dataset_variant: `boruta_all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | regression | boruta_all | long_only_sign | 5.000000 | 0.814377 | 0.814377 | 0.000000 | 4.944569 | 0.166947 | 0.354007 | -0.717392 | 0.142857 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | regression | boruta_all | quantile_long_only_0.20 | 5.000000 | 0.200989 | 0.200989 | 0.000000 | 3.843096 | 0.146417 | 0.563396 | -0.538145 | 0.131467 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
