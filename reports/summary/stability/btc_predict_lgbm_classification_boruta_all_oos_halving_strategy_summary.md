# Halving Period and Strategy Study

- model: `lgbm`
- task: `classification`
- dataset_variant: `boruta_all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | classification | boruta_all | long_only_sign | 5.000000 | 0.786471 | 0.786471 | 0.000000 | 2.778367 | 0.122028 | 0.254740 | -0.704871 | 0.185572 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | classification | boruta_all | quantile_long_only_0.20 | 5.000000 | 0.204345 | 0.204345 | 0.000000 | 2.166194 | 0.104980 | 0.396012 | -0.535764 | 0.177504 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
