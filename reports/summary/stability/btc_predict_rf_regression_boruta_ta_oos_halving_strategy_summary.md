# Halving Period and Strategy Study

- model: `rf`
- task: `regression`
- dataset_variant: `boruta_ta`
- prediction_scope: `oos`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | boruta_ta | long_only_sign | 5.000000 | 0.415048 | 0.415048 | 0.000000 | 1.909221 | 0.096909 | 0.298208 | -0.706170 | 0.096346 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | rf | regression | boruta_ta | long_only_band_0.01 | 5.000000 | 0.013246 | 0.013246 | 0.000000 | 0.484449 | 0.034809 | 0.342411 | -0.174019 | 0.010916 | 4214 |

## Fixed Halving Periods

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
