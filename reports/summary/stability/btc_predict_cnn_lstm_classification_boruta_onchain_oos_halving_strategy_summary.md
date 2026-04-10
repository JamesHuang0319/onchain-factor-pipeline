# Halving Period and Strategy Study

- model: `cnn_lstm`
- task: `classification`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | cnn_lstm | classification | boruta_onchain | sign_band_0.0025 | 2018-03-17 | 5.000000 | 0.992406 | 0.935359 | 0.057047 | 18.075573 | 0.290951 | 0.554663 | -0.692053 | 0.077836 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | cnn_lstm | classification | boruta_onchain | sign_band_0.0025 | 2018-03-17 | 5.000000 | 0.992406 | 0.935359 | 0.057047 | 18.075573 | 0.290951 | 0.554663 | -0.692053 | 0.077836 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
