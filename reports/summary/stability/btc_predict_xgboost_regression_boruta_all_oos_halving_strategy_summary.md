# Halving Period and Strategy Study

- model: `xgboost`
- task: `regression`
- dataset_variant: `boruta_all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | boruta_all | sign_band_0.0025 | 5.000000 | 0.541858 | 0.327976 | 0.213882 | 8.828730 | 0.218895 | 0.516070 | -0.659233 | 0.391077 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | boruta_all | quantile_long_only_0.20 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 7.344911 | 0.201738 | 0.767356 | -0.406193 | 0.150925 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
