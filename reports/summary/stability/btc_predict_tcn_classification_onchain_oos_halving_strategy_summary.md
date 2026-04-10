# Halving Period and Strategy Study

- model: `tcn`
- task: `classification`
- dataset_variant: `onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | tcn | classification | onchain | full_exposure_sign | 2018-03-17 | 5.000000 | 1.000000 | 0.521900 | 0.478100 | 24.505072 | 0.323843 | 0.617029 | -0.671176 | 0.360702 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | tcn | classification | onchain | long_only_sign | 2018-03-17 | 5.000000 | 0.521900 | 0.521900 | 0.000000 | 14.432081 | 0.267467 | 0.692801 | -0.671421 | 0.180351 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
