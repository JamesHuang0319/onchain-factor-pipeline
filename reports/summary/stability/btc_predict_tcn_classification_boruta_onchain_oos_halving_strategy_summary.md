# Halving Period and Strategy Study

- model: `tcn`
- task: `classification`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | tcn | classification | boruta_onchain | long_only_band_0.01 | 2018-03-17 | 5.000000 | 0.713705 | 0.713705 | 0.000000 | 7.172919 | 0.199573 | 0.448372 | -0.649400 | 0.198386 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | tcn | classification | boruta_onchain | quantile_long_only_0.10 | 2018-03-17 | 5.000000 | 0.100141 | 0.100141 | 0.000000 | 6.001608 | 0.183607 | 0.962938 | -0.244115 | 0.093498 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
