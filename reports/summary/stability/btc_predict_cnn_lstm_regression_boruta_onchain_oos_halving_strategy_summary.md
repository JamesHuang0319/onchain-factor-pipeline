# Halving Period and Strategy Study

- model: `cnn_lstm`
- task: `regression`
- dataset_variant: `boruta_onchain`
- prediction_scope: `oos`
- prediction_start: `2018-03-17`
- cost_bps: `5.0`

## Best by Cumulative Return

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | cnn_lstm | regression | boruta_onchain | full_exposure_sign | 2018-03-17 | 5.000000 | 1.000000 | 0.501413 | 0.498587 | 14.686470 | 0.269263 | 0.512787 | -0.689641 | 0.386331 | 4214 |

## Best by Sharpe

| prediction_scope | model | task | variant | strategy | prediction_start | cost_bps | exposure_rate | long_rate | short_rate | cumulative_return | annualised_return | sharpe_ratio | max_drawdown | turnover | n_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oos | cnn_lstm | regression | boruta_onchain | quantile_ls_0.20 | 2018-03-17 | 5.000000 | 0.400212 | 0.200106 | 0.200106 | 11.249836 | 0.242366 | 0.662843 | -0.638732 | 0.268628 | 4214 |

## Fixed Halving Periods

- `full_sample` (strategy active from `2018-03-17`)
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`
