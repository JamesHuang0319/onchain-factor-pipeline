# Halving Period and Strategy Study

- model: `lstm`
- task: `classification`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lstm | classification | boruta_onchain | full_exposure_sign | 2018-03-17 | 5.000000 | 1.000000 | 0.879018 | 0.120982 | 17.265796 | 0.286110 | 0.544453 | -0.671666 | 0.155197 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lstm | classification | boruta_onchain | quantile_long_only_0.20 | 2018-03-17 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 6.619674 | 0.192312 | 0.762897 | -0.338662 | 0.076412 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
