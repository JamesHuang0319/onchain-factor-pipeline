# Halving Period and Strategy Study

- model: `xgboost`
- task: `regression`
- dataset_variant: `all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | all | quantile_ls_0.10 | 5.000000 | 0.200283 | 0.100141 | 0.100141 | 14.665997 | 0.269120 | 0.841205 | -0.321683 | 0.168011 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | all | quantile_ls_0.10 | 5.000000 | 0.200283 | 0.100141 | 0.100141 | 14.665997 | 0.269120 | 0.841205 | -0.321683 | 0.168011 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
