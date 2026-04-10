# Halving Period and Strategy Study

- model: `svm`
- task: `regression`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | svm | regression | boruta_onchain | full_exposure_sign | 2018-03-17 | 5.000000 | 1.000000 | 0.543624 | 0.456376 | 50.695987 | 0.407385 | 0.774842 | -0.745159 | 0.491220 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | svm | regression | boruta_onchain | quantile_long_only_0.20 | 2018-03-17 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 10.928815 | 0.239512 | 0.922139 | -0.504305 | 0.156621 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
