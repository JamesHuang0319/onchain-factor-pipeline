# Halving Period and Strategy Study

- model: `rf`
- task: `classification`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | boruta_onchain | sign_band_0.005 | 2018-03-17 | 5.000000 | 0.915401 | 0.624514 | 0.290887 | 40.346432 | 0.380414 | 0.756105 | -0.627467 | 0.506882 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | boruta_onchain | quantile_long_only_0.05 | 2018-03-17 | 5.000000 | 0.050159 | 0.050159 | 0.000000 | 4.176838 | 0.153053 | 1.045003 | -0.160599 | 0.049359 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
