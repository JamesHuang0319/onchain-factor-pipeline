# Halving Period and Strategy Study

- model: `rf`
- task: `regression`
- dataset_variant: `ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | ta | sign_band_0.0025 | 5.000000 | 0.503532 | 0.229954 | 0.273578 | 12.099170 | 0.249601 | 0.574274 | -0.852050 | 0.167062 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | ta | long_only_band_0.0025 | 5.000000 | 0.229954 | 0.229954 | 0.000000 | 7.123173 | 0.198938 | 0.784412 | -0.478043 | 0.089226 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
