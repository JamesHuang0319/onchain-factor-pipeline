# Halving Period and Strategy Study

- model: `rf`
- task: `classification`
- dataset_variant: `ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | ta | sign_band_0.01 | 5.000000 | 0.911339 | 0.458319 | 0.453020 | 20.531790 | 0.304566 | 0.603725 | -0.673750 | 0.431894 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | ta | long_only_band_0.01 | 5.000000 | 0.458319 | 0.458319 | 0.000000 | 11.437082 | 0.243999 | 0.667921 | -0.632395 | 0.216896 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
