# Halving Period and Strategy Study

- model: `lgbm`
- task: `classification`
- dataset_variant: `univariate`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | classification | univariate | long_only_band_0.01 | 5.000000 | 0.711409 | 0.711409 | 0.000000 | 3.934672 | 0.148279 | 0.317521 | -0.719648 | 0.063123 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | classification | univariate | long_only_band_0.01 | 5.000000 | 0.711409 | 0.711409 | 0.000000 | 3.934672 | 0.148279 | 0.317521 | -0.719648 | 0.063123 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
