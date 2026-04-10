# Halving Period and Strategy Study

- model: `xgboost`
- task: `classification`
- dataset_variant: `boruta_ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | classification | boruta_ta | long_only_band_0.01 | 5.000000 | 0.482515 | 0.482515 | 0.000000 | 3.982787 | 0.149244 | 0.425802 | -0.563506 | 0.275748 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | classification | boruta_ta | long_only_band_0.01 | 5.000000 | 0.482515 | 0.482515 | 0.000000 | 3.982787 | 0.149244 | 0.425802 | -0.563506 | 0.275748 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
