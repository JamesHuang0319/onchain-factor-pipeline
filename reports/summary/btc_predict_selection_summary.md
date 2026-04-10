# Selection Summary

- config_name: `onchain_crypto_graduation_research`
- artifact_prefix: `btc_predict`
- summary_cost_bps: `5.0`

## Rules

- Classification experiment winner: highest F1.
- Regression experiment winner: lowest RMSE, tie-break by IC then trading score.
- Return winner: highest cumulative return, tie-break by Sharpe then drawdown.
- Final return model: regression return winner.

| selection_type | task | model | variant | selected_feature_count | predictive_score | trading_score | cumulative_return | sharpe_ratio | max_drawdown | rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| classification_experiment_winner | classification | svm | boruta_onchain | 22 | 0.676484 | -0.579242 | -0.579242 | -0.224912 | -0.776054 | classification: highest F1; regression: lowest RMSE, tie-break by IC then trading score |
| classification_return_winner | classification | rf | boruta_onchain | 22 | 0.599970 | 20.465044 | 20.465044 | 0.848491 | -0.435260 | highest cumulative return, tie-break by Sharpe then drawdown |
| regression_experiment_winner | regression | lasso | boruta_all | 78 | -0.027773 |  |  |  |  | classification: highest F1; regression: lowest RMSE, tie-break by IC then trading score |
| regression_return_winner | regression | rf | boruta_onchain | 6 | -0.033031 | 13.212349 | 13.212349 | 0.694479 | -0.637029 | highest cumulative return, tie-break by Sharpe then drawdown |
| final_return_model | regression | rf | boruta_onchain | 6 | -0.033031 | 13.212349 | 13.212349 | 0.694479 | -0.637029 | final model for return prediction: regression return winner |
