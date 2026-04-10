# Halving Period and Strategy Study

- model: `xgboost`
- task: `classification`
- dataset_variant: `all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | classification | all | quantile_ls_0.20 | 5.000000 | 0.400212 | 0.200106 | 0.200106 | 12.858658 | 0.255716 | 0.732996 | -0.537806 | 0.358804 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | classification | all | quantile_long_only_0.20 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 11.563627 | 0.245091 | 0.910588 | -0.361828 | 0.186996 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
