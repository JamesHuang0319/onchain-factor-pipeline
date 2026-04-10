# Halving Period and Strategy Study

- model: `gru`
- task: `classification`
- dataset_variant: `onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | gru | classification | onchain | quantile_ls_0.05 | 2018-03-17 | 5.000000 | 0.100318 | 0.050159 | 0.050159 | 3.797345 | 0.145475 | 0.570664 | -0.444953 | 0.045088 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | gru | classification | onchain | quantile_long_only_0.05 | 2018-03-17 | 5.000000 | 0.050159 | 0.050159 | 0.000000 | 2.064296 | 0.101854 | 0.722704 | -0.187741 | 0.018984 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
