# crypto_predict

基于链上数据的 BTC 收益预测研究项目。当前仓库已经形成一条完整、可复现的研究流水线，覆盖数据下载、特征构建、特征筛选、时间序列训练、回测、报告生成、实验汇总和最新样本预测。

## 当前阶段

- 研究对象：`BTC-USD`
- 主数据源：`Coin Metrics Community API`
- 兼容数据源：`Blockchain.com`
- 当前标签：
  - `classification`：次日涨跌方向
  - `regression`：次日对数收益率 `log_ret_h`
- 当前核心数据集：
  - `onchain`
  - `ta`
  - `all`
  - `boruta_onchain`
  - `boruta_ta`
  - `boruta_all`
  - `univariate`
- 输出前缀：`btc_predict`

当前项目已经完成第一阶段主实验，重点转入“固定最优基线 + 扩展链上因子增量验证”。

## 已实现能力

- 数据下载：价格数据 + 链上数据
- 特征工程：价格、TA、链上因子与交叉因子
- 特征筛选：`boruta_*`
  - 说明：当前是 `Boruta-like RF importance + Lasso/L1` 两阶段筛选，不是标准 Boruta 逐项复现
- 时间序列训练：walk-forward
- 自动回测与报告生成
- 最终模型保存与最新样本预测
- 实验总表与模型选择结果自动汇总
- 批量调参与批量实验脚本

## 已实现模型

机器学习模型：

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

说明：

- `xgboost` 属于树模型的梯度提升方法，不是深度学习。
- 当前主线仍然是 `ML`，`DL` 已完成基线实现，但不是现阶段最优收益模型。

## 当前阶段结果

汇总文件：

- [btc_predict_experiment_summary.csv](E:\Python_workplace\crypto_predict\reports\summary\btc_predict_experiment_summary.csv)
- [btc_predict_experiment_summary.md](E:\Python_workplace\crypto_predict\reports\summary\btc_predict_experiment_summary.md)
- [btc_predict_selection_summary.csv](E:\Python_workplace\crypto_predict\reports\summary\btc_predict_selection_summary.csv)
- [btc_predict_selection_summary.md](E:\Python_workplace\crypto_predict\reports\summary\btc_predict_selection_summary.md)

当前按既定规则得到的阶段性结论：

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

这说明在当前这套数据、特征和验证框架下：

- `SVM` 更像分类实验强者
- `RF` 是最稳的收益主线
- `boruta_onchain` 是当前最有价值的数据集版本
- `XGBoost` 和 `LightGBM` 已完成完整实验，但尚未超过当前最优 `RF`

## 最小运行流程

```bash
python -m src.cli download-data --config configs/experiment.yaml
python -m src.cli build-features --config configs/experiment.yaml
python -m src.cli data-audit --config configs/experiment.yaml --dataset-variant all
python -m src.cli validate --config configs/experiment.yaml
```

单组实验：

```bash
python -m src.cli train --config configs/experiment.yaml --model rf --task regression --dataset-variant boruta_onchain
python -m src.cli backtest --config configs/experiment.yaml --model rf --task regression --dataset-variant boruta_onchain
python -m src.cli report --config configs/experiment.yaml --model rf --task regression --dataset-variant boruta_onchain
```

最新样本预测：

```bash
python -m src.cli predict-latest --config configs/experiment.yaml --model rf --task regression --dataset-variant boruta_onchain
```

刷新实验总表：

```bash
python -m src.cli experiment-summary --config configs/experiment.yaml --cost-bps 5
```

## 批量调参与批量实验

核心批量实验脚本：

- [run_core_experiments.ps1](E:\Python_workplace\crypto_predict\scripts\run_core_experiments.ps1)
- [run_ml_tuning_full.ps1](E:\Python_workplace\crypto_predict\scripts\run_ml_tuning_full.ps1)

完整 `RF / XGBoost / LightGBM` 调参与实验：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_ml_tuning_full.ps1 -Models rf,xgboost,lgbm -Trials 20
```

脚本会输出：

- 当前进度
- 已耗时
- 平均每组耗时
- 预计剩余时间
- 每组状态与日志

## 主要输出目录

- `data/features/`
  - 特征集、预测结果、指标 JSON、回测产物
- `models_saved/`
  - 最终模型与元信息
- `reports/summary/`
  - 汇总表、阶段报告、最新预测、选择结果，以及按主题分组的子目录
- `reports/figures/`
  - Equity、Drawdown、Pred vs Actual 图
- `reports/trading/`
  - 交互式交易图
- `reports/batch_runs/`
  - 批量实验日志和批次汇总

## 当前研究主线

当前最重要的问题已经不是继续补流程，而是回答下面三个问题：

1. 链上因子相对纯价格/TA 是否存在稳定增量价值
2. 方向预测与幅度预测，哪一条线更适合交易
3. 在现有数据和验证框架下，哪种模型最稳、最能转化为收益

当前建议顺序：

1. 固定当前最优 `RF` 基线
2. 扩有历史数据的链上因子
3. 与当前基线做增量比较
4. 再决定是否继续做更深的模型优化

## 文档

- [PROJECT_PLAN.md](E:\Python_workplace\crypto_predict\docs\PROJECT_PLAN.md)
- [DATA_FOUNDATION_PLAN.md](E:\Python_workplace\crypto_predict\docs\DATA_FOUNDATION_PLAN.md)
- [METHODOLOGY.md](E:\Python_workplace\crypto_predict\docs\METHODOLOGY.md)
- [EXPERIMENTS.md](E:\Python_workplace\crypto_predict\docs\EXPERIMENTS.md)
- [THESIS_NOTES.md](E:\Python_workplace\crypto_predict\docs\THESIS_NOTES.md)
- [REPO_LAYOUT.md](E:\Python_workplace\crypto_predict\docs\REPO_LAYOUT.md)

## 说明

- 本项目当前是 `paper-guided`，不是参考论文的逐项严格复现。
- 模型判断不能只看单一指标，应同时看：
  - 预测指标
  - 收益表现
  - Sharpe
  - Max Drawdown
  - 成本敏感性
