# Halving Period and Strategy Study

- model: `rf`
- task: `classification`
- dataset_variant: `all`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | all | long_only_band_0.005 | 5.000000 | 0.592370 | 0.592370 | 0.000000 | 6.371619 | 0.188899 | 0.464520 | -0.731714 | 0.266255 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | classification | all | long_only_band_0.005 | 5.000000 | 0.592370 | 0.592370 | 0.000000 | 6.371619 | 0.188899 | 0.464520 | -0.731714 | 0.266255 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
