# Halving Period and Strategy Study

- model: `cnn_lstm`
- task: `classification`
- dataset_variant: `onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | cnn_lstm | classification | onchain | quantile_long_only_0.10 | 2018-03-17 | 5.000000 | 0.100141 | 0.100141 | 0.000000 | 2.627406 | 0.118073 | 0.677264 | -0.268267 | 0.085430 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | cnn_lstm | classification | onchain | quantile_long_only_0.10 | 2018-03-17 | 5.000000 | 0.100141 | 0.100141 | 0.000000 | 2.627406 | 0.118073 | 0.677264 | -0.268267 | 0.085430 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
