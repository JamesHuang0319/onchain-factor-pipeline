# Halving Period and Strategy Study

- model: `rf`
- task: `regression`
- dataset_variant: `boruta_all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | boruta_all | sign_band_0.0025 | 5.000000 | 0.304663 | 0.248146 | 0.056517 | 30.193974 | 0.347133 | 1.011175 | -0.471968 | 0.177504 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | boruta_all | sign_band_0.0025 | 5.000000 | 0.304663 | 0.248146 | 0.056517 | 30.193974 | 0.347133 | 1.011175 | -0.471968 | 0.177504 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
