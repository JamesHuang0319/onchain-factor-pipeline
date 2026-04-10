# Halving Period and Strategy Study

- model: `svm`
- task: `classification`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | svm | classification | boruta_onchain | long_only_band_0.0025 | 2018-03-17 | 5.000000 | 0.997527 | 0.997527 | 0.000000 | 9.193894 | 0.222752 | 0.423723 | -0.766346 | 0.003797 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | svm | classification | boruta_onchain | long_only_band_0.0025 | 2018-03-17 | 5.000000 | 0.997527 | 0.997527 | 0.000000 | 9.193894 | 0.222752 | 0.423723 | -0.766346 | 0.003797 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
