# Halving Period and Strategy Study

- model: `rf`
- task: `classification`
- dataset_variant: `onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | onchain | full_exposure_sign | 2018-03-17 | 5.000000 | 1.000000 | 0.608089 | 0.391911 | 9.156964 | 0.222368 | 0.423565 | -0.721866 | 0.506407 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | onchain | long_only_sign | 2018-03-17 | 5.000000 | 0.608089 | 0.608089 | 0.000000 | 8.743395 | 0.217974 | 0.533894 | -0.715833 | 0.252966 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
