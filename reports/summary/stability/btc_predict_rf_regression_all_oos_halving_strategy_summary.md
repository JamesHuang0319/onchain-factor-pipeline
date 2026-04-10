# Halving Period and Strategy Study

- model: `rf`
- task: `regression`
- dataset_variant: `all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | all | quantile_ls_0.20 | 5.000000 | 0.400212 | 0.200106 | 0.200106 | 4.701969 | 0.162743 | 0.422288 | -0.761102 | 0.182250 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | all | quantile_long_only_0.20 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 3.033693 | 0.128401 | 0.589334 | -0.360031 | 0.095396 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
