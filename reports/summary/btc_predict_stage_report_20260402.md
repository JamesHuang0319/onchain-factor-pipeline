# Stage Report

- date: `2026-04-02`
- project: `crypto_predict`
- artifact_prefix: `btc_predict`
- subject: `BTC-USD`

## Scope

本阶段目标是把项目从“单点实验”推进到“完整研究流水线”，并完成机器学习主线的完整比较。

已完成范围：

- 数据下载与缓存
- 链上数据主源切换到 `Coin Metrics`
- 特征构建与时间对齐
- `Boruta-like + Lasso/L1` 两阶段特征筛选
- `train / backtest / report / predict-latest / experiment-summary`
- 最终模型保存与加载
- 批量调参框架
- `RF / XGBoost / LightGBM` 全量实验
- `SVM` 核心实验
- `DL` 基线模型落地

## Implemented Pipeline

当前主流程已经打通：

1. `download-data`
2. `build-features`
3. `data-audit`
4. `validate`
5. `tune`
6. `train`
7. `backtest`
8. `report`
9. `experiment-summary`
10. `predict-latest`

这意味着项目已经从“搭框架”阶段进入“固定基线并做增量研究”阶段。

## Model Coverage

机器学习：

- `svm`
- `rf`
- `lgbm`
- `xgboost`
- `lasso`
- `ridge`

深度学习基线：

- `lstm`
- `cnn_lstm`
- `gru`
- `tcn`

## Dataset Variants

- `onchain`
- `ta`
- `all`
- `boruta_onchain`
- `boruta_ta`
- `boruta_all`
- `univariate`

当前最有价值的数据集版本是 `boruta_onchain`。

## Stage Findings

基于 [btc_predict_selection_summary.csv](E:\Python_workplace\crypto_predict\reports\00_summary\btc_predict_selection_summary.csv)：

- 分类实验冠军：`svm + boruta_onchain`
  - `F1 = 0.6765`
- 分类收益冠军：`rf + boruta_onchain`
  - `F1 = 0.6000`
  - `5bps cumulative_return = 20.4650`
  - `Sharpe = 0.8485`
- 回归实验冠军：`lasso + boruta_all`
  - `RMSE = 0.02777`
- 回归收益冠军：`rf + boruta_onchain`
  - `RMSE = 0.03303`
  - `5bps cumulative_return = 13.2123`
  - `Sharpe = 0.6945`
- 当前最终收益模型：`rf + regression + boruta_onchain`

关键判断：

- `SVM` 更适合作为分类实验对照，不适合作为当前最终收益模型。
- `RF` 是当前最稳的收益主线。
- `XGBoost` 和 `LightGBM` 已完整跑通，但尚未超过当前最优 `RF`。
- `DL` 已有基线，但当前仍弱于主力 `ML` 模型。

## Interpretation

当前结果说明：

1. 链上因子本身具有预测价值。
2. 经过特征筛选后，链上因子块比原始全量特征更稳。
3. 最优收益模型并不等于最优预测指标模型。
4. 当前最值得固定的主基线不是 `SVM`，而是 `RF + boruta_onchain`。

## Next Stage

下一阶段不再继续铺更多模型，而是：

1. 固定当前 `RF` 最优基线
2. 扩展有历史数据支撑的链上因子
3. 与当前基线做增量比较
4. 再评估是否有必要继续深挖 `XGBoost / LightGBM / DL`

## Key Files

- [README.md](E:\Python_workplace\crypto_predict\README.md)
- [experiment.yaml](E:\Python_workplace\crypto_predict\configs\experiment.yaml)
- [btc_predict_experiment_summary.csv](E:\Python_workplace\crypto_predict\reports\00_summary\btc_predict_experiment_summary.csv)
- [btc_predict_selection_summary.csv](E:\Python_workplace\crypto_predict\reports\00_summary\btc_predict_selection_summary.csv)
- [run_ml_tuning_full.ps1](E:\Python_workplace\crypto_predict\scripts\run_ml_tuning_full.ps1)
