# Halving Period and Strategy Study

- model: `gru`
- task: `classification`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | gru | classification | boruta_onchain | long_only_band_0.01 | 2018-03-17 | 5.000000 | 0.672377 | 0.672377 | 0.000000 | 14.884654 | 0.270644 | 0.663164 | -0.607221 | 0.145230 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | gru | classification | boruta_onchain | quantile_long_only_0.10 | 2018-03-17 | 5.000000 | 0.100141 | 0.100141 | 0.000000 | 3.158016 | 0.131372 | 0.723786 | -0.241406 | 0.052682 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
