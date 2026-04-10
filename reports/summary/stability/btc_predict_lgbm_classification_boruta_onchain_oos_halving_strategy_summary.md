# Halving Period and Strategy Study

- model: `lgbm`
- task: `classification`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | classification | boruta_onchain | long_only_band_0.01 | 2018-03-17 | 5.000000 | 0.714942 | 0.714942 | 0.000000 | 2.340230 | 0.110114 | 0.247537 | -0.707346 | 0.227337 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | classification | boruta_onchain | quantile_long_only_0.05 | 2018-03-17 | 5.000000 | 0.050159 | 0.050159 | 0.000000 | 0.418100 | 0.030719 | 0.250575 | -0.183007 | 0.062648 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
