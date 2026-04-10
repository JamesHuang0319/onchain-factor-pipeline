# Halving Period and Strategy Study

- model: `lgbm`
- task: `classification`
- dataset_variant: `ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | classification | ta | long_only_band_0.005 | 5.000000 | 0.699046 | 0.699046 | 0.000000 | 7.872952 | 0.208142 | 0.478483 | -0.729469 | 0.192691 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | lgbm | classification | ta | long_only_band_0.005 | 5.000000 | 0.699046 | 0.699046 | 0.000000 | 7.872952 | 0.208142 | 0.478483 | -0.729469 | 0.192691 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
