# Halving Period and Strategy Study

- model: `xgboost`
- task: `classification`
- dataset_variant: `boruta_all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | classification | boruta_all | full_exposure_sign | 5.000000 | 1.000000 | 0.537443 | 0.462557 | 8.381074 | 0.213983 | 0.407896 | -0.854505 | 0.554817 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | classification | boruta_all | quantile_ls_0.10 | 5.000000 | 0.200283 | 0.100141 | 0.100141 | 5.770413 | 0.180170 | 0.715908 | -0.413047 | 0.218320 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
