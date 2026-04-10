# Halving Period and Strategy Study

- model: `xgboost`
- task: `classification`
- dataset_variant: `ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | classification | ta | long_only_band_0.0025 | 5.000000 | 0.498764 | 0.498764 | 0.000000 | 3.571570 | 0.140702 | 0.370940 | -0.685605 | 0.250119 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | classification | ta | quantile_long_only_0.20 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 2.236440 | 0.107083 | 0.433891 | -0.476584 | 0.150925 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
