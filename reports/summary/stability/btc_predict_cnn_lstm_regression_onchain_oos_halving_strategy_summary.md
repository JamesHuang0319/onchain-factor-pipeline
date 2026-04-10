# Halving Period and Strategy Study

- model: `cnn_lstm`
- task: `regression`
- dataset_variant: `onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | cnn_lstm | regression | onchain | long_only_sign | 2018-03-17 | 5.000000 | 0.648887 | 0.648887 | 0.000000 | 2.669980 | 0.119203 | 0.286920 | -0.658423 | 0.184148 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | cnn_lstm | regression | onchain | long_only_sign | 2018-03-17 | 5.000000 | 0.648887 | 0.648887 | 0.000000 | 2.669980 | 0.119203 | 0.286920 | -0.658423 | 0.184148 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
