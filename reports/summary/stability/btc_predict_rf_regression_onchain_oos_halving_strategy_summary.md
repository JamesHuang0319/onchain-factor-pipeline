# Halving Period and Strategy Study

- model: `rf`
- task: `regression`
- dataset_variant: `onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | onchain | long_only_sign | 2018-03-17 | 5.000000 | 0.462557 | 0.462557 | 0.000000 | 1.200272 | 0.070691 | 0.217005 | -0.680723 | 0.184623 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | onchain | quantile_long_only_0.05 | 2018-03-17 | 5.000000 | 0.050159 | 0.050159 | 0.000000 | 0.328452 | 0.024905 | 0.335177 | -0.182692 | 0.024680 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
