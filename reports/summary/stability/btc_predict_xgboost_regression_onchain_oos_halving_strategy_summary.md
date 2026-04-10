# Halving Period and Strategy Study

- model: `xgboost`
- task: `regression`
- dataset_variant: `onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | onchain | full_exposure_sign | 2018-03-17 | 5.000000 | 1.000000 | 0.527375 | 0.472625 | 10.090805 | 0.231716 | 0.440170 | -0.836887 | 0.525392 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | xgboost | regression | onchain | quantile_long_only_0.05 | 2018-03-17 | 5.000000 | 0.050159 | 0.050159 | 0.000000 | 2.087990 | 0.102589 | 0.744167 | -0.132160 | 0.052207 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
