# Halving Period and Strategy Study

- model: `rf`
- task: `regression`
- dataset_variant: `univariate`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | univariate | quantile_long_only_0.05 | 5.000000 | 0.050336 | 0.050336 | 0.000000 | -0.381141 | -0.040713 | -0.314581 | -0.448694 | 0.031799 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | univariate | long_only_sign | 5.000000 | 0.492582 | 0.492582 | 0.000000 | -0.452008 | -0.050765 | -0.138372 | -0.740543 | 0.123873 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
