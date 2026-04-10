# Halving Period and Strategy Study

- model: `lstm`
- task: `regression`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lstm | regression | boruta_onchain | sign_band_0.0025 | 2018-03-17 | 5.000000 | 0.614800 | 0.347227 | 0.267573 | 22.970445 | 0.316746 | 0.716948 | -0.589143 | 0.393925 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lstm | regression | boruta_onchain | quantile_long_only_0.20 | 2018-03-17 | 5.000000 | 0.200106 | 0.200106 | 0.000000 | 6.911725 | 0.196202 | 0.757851 | -0.480262 | 0.154722 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
