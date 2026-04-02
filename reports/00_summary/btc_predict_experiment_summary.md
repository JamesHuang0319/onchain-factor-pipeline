# Experiment Summary

- config_name: `onchain_crypto_graduation_research`
- artifact_prefix: `btc_predict`
- summary_cost_bps: `5.0`

## Classification

| model | variant | selected_feature_count | predictive_rank | trading_rank | cnn_lstm_classification_oos_accuracy | cnn_lstm_classification_oos_precision | cnn_lstm_classification_oos_recall | cnn_lstm_classification_oos_f1 | gru_classification_oos_accuracy | gru_classification_oos_precision | gru_classification_oos_recall | gru_classification_oos_f1 | lgbm_classification_oos_accuracy | lgbm_classification_oos_precision | lgbm_classification_oos_recall | lgbm_classification_oos_f1 | lstm_classification_oos_accuracy | lstm_classification_oos_precision | lstm_classification_oos_recall | lstm_classification_oos_f1 | rf_classification_oos_accuracy | rf_classification_oos_precision | rf_classification_oos_recall | rf_classification_oos_f1 | svm_classification_oos_accuracy | svm_classification_oos_precision | svm_classification_oos_recall | svm_classification_oos_f1 | tcn_classification_oos_accuracy | tcn_classification_oos_precision | tcn_classification_oos_recall | tcn_classification_oos_f1 | cumulative_return | annualised_return | sharpe_ratio | max_drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rf | boruta_onchain | 22 | 11.000000 | 1.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.523490 | 0.534875 | 0.519350 | 0.526999 |  |  |  |  |  |  |  |  | 11.182039 | 0.241769 | 0.668837 | -0.655461 |
| rf | boruta_all | 28 | 10.000000 | 2.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.532321 | 0.540945 | 0.561507 | 0.551034 |  |  |  |  |  |  |  |  | 8.386668 | 0.214046 | 0.621966 | -0.540994 |
| rf | all | 78 | 9.000000 | 3.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.524550 | 0.532023 | 0.579820 | 0.554894 |  |  |  |  |  |  |  |  | 4.003180 | 0.149651 | 0.408010 | -0.601231 |
| rf | onchain | 58 | 12.000000 | 4.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.507594 | 0.517749 | 0.534209 | 0.525850 |  |  |  |  |  |  |  |  | 0.842840 | 0.054376 | 0.157319 | -0.776264 |
| lgbm | boruta_onchain | 22 | 6.000000 | 5.000000 |  |  |  |  |  |  |  |  | 0.521547 | 0.519914 | 0.834485 | 0.640669 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.646665 | 0.044147 | 0.125216 | -0.730371 |
| cnn_lstm | onchain | 58 | 14.000000 | 6.000000 | 0.494878 | 0.505751 | 0.516586 | 0.511111 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.401797 | 0.029687 | 0.079054 | -0.731888 |
| gru | onchain | 58 | 15.000000 | 7.000000 |  |  |  |  | 0.497704 | 0.508922 | 0.492744 | 0.500702 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.180731 | 0.014494 | 0.039467 | -0.678837 |
| svm | boruta_all | 28 | 2.000000 | 8.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.517485 | 0.515163 | 0.950933 | 0.668286 |  |  |  |  | -0.372321 | -0.039537 | -0.114906 | -0.800614 |
| lstm | onchain | 58 | 16.000000 | 9.000000 |  |  |  |  |  |  |  |  |  |  |  |  | 0.496291 | 0.507495 | 0.491361 | 0.499298 |  |  |  |  |  |  |  |  |  |  |  |  | -0.468071 | -0.053208 | -0.141652 | -0.783593 |
| lgbm | onchain | 58 | 3.000000 | 10.000000 |  |  |  |  |  |  |  |  | 0.524020 | 0.520605 | 0.868694 | 0.651042 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | -0.511404 | -0.060151 | -0.172223 | -0.822612 |
| tcn | onchain | 58 | 13.000000 | 11.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.503356 | 0.513898 | 0.523842 | 0.518823 | -0.674263 | -0.092584 | -0.279542 | -0.779504 |
| svm | boruta_onchain | 22 | 1.000000 | 12.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.509184 | 0.510299 | 0.984451 | 0.672172 |  |  |  |  | -0.689410 | -0.096319 | -0.302533 | -0.810382 |
| lgbm | all | 78 | 7.000000 | 13.000000 |  |  |  |  |  |  |  |  | 0.516602 | 0.516649 | 0.841742 | 0.640294 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | -0.702827 | -0.099769 | -0.286781 | -0.892087 |
| lgbm | boruta_all | 28 | 5.000000 | 14.000000 |  |  |  |  |  |  |  |  | 0.512716 | 0.514007 | 0.855909 | 0.642292 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | -0.784581 | -0.124509 | -0.371700 | -0.901178 |
| svm | onchain | 58 | 4.000000 | 15.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.508478 | 0.510988 | 0.891845 | 0.649717 |  |  |  |  | -0.813358 | -0.135316 | -0.417468 | -0.860287 |
| svm | all | 78 | 8.000000 | 16.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.506005 | 0.510073 | 0.848652 | 0.637177 |  |  |  |  | -0.874448 | -0.164505 | -0.536717 | -0.914917 |

## Regression

| model | variant | selected_feature_count | predictive_rank | trading_rank | cnn_lstm_regression_oos_mae | cnn_lstm_regression_oos_rmse | cnn_lstm_regression_oos_ic | cnn_lstm_regression_oos_rank_ic | gru_regression_oos_mae | gru_regression_oos_rmse | gru_regression_oos_ic | gru_regression_oos_rank_ic | lasso_regression_oos_mae | lasso_regression_oos_rmse | lasso_regression_oos_ic | lasso_regression_oos_rank_ic | lgbm_regression_oos_mae | lgbm_regression_oos_rmse | lgbm_regression_oos_ic | lgbm_regression_oos_rank_ic | lstm_regression_oos_mae | lstm_regression_oos_rmse | lstm_regression_oos_ic | lstm_regression_oos_rank_ic | rf_regression_oos_mae | rf_regression_oos_rmse | rf_regression_oos_ic | rf_regression_oos_rank_ic | svm_regression_oos_mae | svm_regression_oos_rmse | svm_regression_oos_ic | svm_regression_oos_rank_ic | tcn_regression_oos_mae | tcn_regression_oos_rmse | tcn_regression_oos_ic | tcn_regression_oos_rank_ic | cumulative_return | annualised_return | sharpe_ratio | max_drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rf | boruta_all | 8 | 6.000000 | 1.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.022425 | 0.033205 | 0.091554 | 0.021670 |  |  |  |  |  |  |  |  | 17.678306 | 0.288600 | 0.738496 | -0.502557 |
| rf | boruta_onchain | 6 | 8.000000 | 2.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.022555 | 0.033482 | 0.065751 | 0.027758 |  |  |  |  |  |  |  |  | 9.087867 | 0.221645 | 0.617376 | -0.712289 |
| lgbm | onchain | 58 | 3.000000 | 3.000000 |  |  |  |  |  |  |  |  |  |  |  |  | 0.021957 | 0.033108 | 0.021269 | 0.012161 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 2.752858 | 0.121370 | 0.335921 | -0.702487 |
| lgbm | boruta_onchain | 6 | 5.000000 | 4.000000 |  |  |  |  |  |  |  |  |  |  |  |  | 0.022106 | 0.033153 | 0.028426 | -0.008098 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1.120535 | 0.067273 | 0.186492 | -0.629653 |
| cnn_lstm | onchain | 58 | 11.000000 | 5.000000 | 0.024051 | 0.035065 | 0.004677 | 0.010409 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.066415 | 0.005585 | 0.014988 | -0.812946 |
| lgbm | all | 78 | 4.000000 | 6.000000 |  |  |  |  |  |  |  |  |  |  |  |  | 0.021959 | 0.033116 | 0.023393 | -0.000437 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.023375 | 0.002003 | 0.005426 | -0.885569 |
| rf | onchain | 58 | 13.000000 | 7.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.025879 | 0.036921 | 0.002530 | 0.001986 |  |  |  |  |  |  |  |  | 0.018504 | 0.001589 | 0.004099 | -0.896249 |
| rf | all | 78 | 12.000000 | 8.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.025789 | 0.036798 | 0.015190 | 0.000989 |  |  |  |  |  |  |  |  | 0.005656 | 0.000489 | 0.001253 | -0.878405 |
| gru | onchain | 58 | 10.000000 | 9.000000 |  |  |  |  | 0.023801 | 0.034727 | 0.002787 | 0.010568 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | -0.026956 | -0.002364 | -0.006486 | -0.616003 |
| lstm | onchain | 58 | 9.000000 | 10.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.023084 | 0.034111 | 0.017594 | 0.024113 |  |  |  |  |  |  |  |  |  |  |  |  | -0.096019 | -0.008705 | -0.023964 | -0.579888 |
| svm | boruta_all | 8 | 15.000000 | 11.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.031246 | 0.045694 | 0.020144 | 0.004415 |  |  |  |  | -0.365122 | -0.038587 | -0.099724 | -0.704872 |
| lgbm | boruta_all | 8 | 7.000000 | 12.000000 |  |  |  |  |  |  |  |  |  |  |  |  | 0.022137 | 0.033219 | 0.002913 | -0.030179 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | -0.503312 | -0.058813 | -0.159210 | -0.794536 |
| tcn | onchain | 58 | 18.000000 | 13.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.041863 | 0.058713 | -0.013543 | -0.012310 | -0.713551 | -0.102630 | -0.301623 | -0.925427 |
| svm | all | 78 | 17.000000 | 14.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.040612 | 0.052904 | -0.012246 | -0.013787 |  |  |  |  | -0.739650 | -0.110025 | -0.321310 | -0.829235 |
| svm | boruta_onchain | 6 | 16.000000 | 15.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.033591 | 0.048984 | -0.027003 | -0.028443 |  |  |  |  | -0.783989 | -0.124301 | -0.355281 | -0.878584 |
| svm | onchain | 58 | 19.000000 | 16.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.045194 | 0.059183 | -0.032065 | -0.029293 |  |  |  |  | -0.830643 | -0.142564 | -0.414431 | -0.873597 |
| lasso | boruta_all | 78 | 1.000000 |  |  |  |  |  |  |  |  |  | 0.019288 | 0.027773 | 0.016520 | 0.008601 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| lgbm | ta | 21 | 2.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.022044 | 0.033097 | 0.039070 | 0.004872 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| svm | ta | 21 | 14.000000 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 0.030647 | 0.044568 | 0.022126 | 0.024023 |  |  |  |  |  |  |  |  |

