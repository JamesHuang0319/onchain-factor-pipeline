# Halving Period and Strategy Study

- model: `rf`
- task: `classification`
- dataset_variant: `boruta_all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | boruta_all | full_exposure_sign | 5.000000 | 1.000000 | 0.571000 | 0.429000 | 29.050180 | 0.342781 | 0.654302 | -0.760335 | 0.517798 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | boruta_all | long_only_sign | 5.000000 | 0.571000 | 0.571000 | 0.000000 | 15.742396 | 0.276445 | 0.689155 | -0.619188 | 0.259136 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
