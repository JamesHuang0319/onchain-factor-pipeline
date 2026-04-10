# Halving Period and Strategy Study

- model: `lgbm`
- task: `regression`
- dataset_variant: `all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | regression | all | full_exposure_sign | 5.000000 | 1.000000 | 0.796892 | 0.203108 | 27.514729 | 0.336695 | 0.640106 | -0.725094 | 0.276697 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | regression | all | full_exposure_sign | 5.000000 | 1.000000 | 0.796892 | 0.203108 | 27.514729 | 0.336695 | 0.640106 | -0.725094 | 0.276697 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
