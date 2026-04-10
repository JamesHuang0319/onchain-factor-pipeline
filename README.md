# crypto_predict

基于链上数据的 BTC 收益预测研究项目。仓库已经形成一条完整、可复现的研究流水线，覆盖数据下载、特征构建、特征筛选、时间序列训练、回测、报告生成、实验汇总、稳健性分析和最新样本预测。

## 项目简介

- 研究对象：`BTC-USD`
- 频率：`日频`
- 主数据源：`Coin Metrics Community API`
- 兼容数据源：`Blockchain.com`
- 当前任务：
  - `classification`：预测次日涨跌方向 `direction_h`
  - `regression`：预测次日对数收益率 `log_ret_h`
- 当前核心特征主线：`boruta_onchain`

项目定位是论文研究流水线，不是纯策略工程仓库。当前重点是比较：

- 链上因子是否具有增量价值
- 方向预测与幅度预测哪条线更适合交易
- `ML` 与 `DL` 在统一 `OOS` 框架下谁更稳、谁上限更高

## 当前状态

已实现能力：

- 数据下载：价格数据 + 链上数据
- 特征工程：价格、TA、链上因子与派生比值/变化率特征
- 特征筛选：`Boruta-like RF importance + Lasso/L1` 两阶段筛选
- 时间序列训练：`walk-forward`
- 自动回测、图表生成、Markdown 报告
- 最终模型保存与最新样本预测
- 实验总表自动汇总
- 固定减半周期稳健性分析
- 固定策略空间搜索
- `ML / DL` 批量调参与批量稳定性脚本

当前论文主线建议：

- 主线：经济价值 / 交易收益
- 副线：方向预测
- 重点特征集：`boruta_onchain`

## 快速开始

### 1. 数据准备

```bash
python -m src.cli download-data --config configs/experiment.yaml
python -m src.cli build-features --config configs/experiment.yaml
python -m src.cli data-audit --config configs/experiment.yaml --dataset-variant all
python -m src.cli validate --config configs/experiment.yaml
```

### 2. 单组实验

```bash
python -m src.cli tune --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
python -m src.cli train --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
python -m src.cli backtest --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
python -m src.cli report --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
```

### 3. 查看调参候选集

```bash
python -m src.cli show-search-space --model rf --task classification
python -m src.cli show-search-space --model tcn --task regression
```

导出成 Markdown：

```bash
python -m src.cli show-search-space --out reports/summary/tuning_search_spaces.md
```

### 4. 稳健性与策略映射

```bash
python -m src.cli halving-strategy-study --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain --cost-bps 5 --prediction-scope oos
```

### 5. 最新样本预测

```bash
python -m src.cli predict-latest --config configs/experiment.yaml --model rf --task regression --dataset-variant boruta_onchain
```

### 6. 刷新实验总表

```bash
python -m src.cli experiment-summary --config configs/experiment.yaml --cost-bps 5
```

## CLI 常用命令

- `download-data`
  - 下载价格和链上数据，带缓存
- `build-features`
  - 构建完整特征数据集
- `data-audit`
  - 输出样本覆盖、标签分布、训练集划分摘要
- `validate`
  - 运行防泄漏检查
- `show-search-space`
  - 查看每个模型/任务的调参候选集
- `tune`
  - 随机搜索超参数，并可自动触发 `train/backtest/report`
- `train`
  - 运行 `walk-forward OOS` 训练并保存预测
- `backtest`
  - 对已保存预测执行回测
- `report`
  - 生成 PDF 图表和 Markdown 报告
- `predict-latest`
  - 用最终模型预测最新样本
- `test-full-history`
  - 用保存的最终模型对完整历史重新打分
- `halving-strategy-study`
  - 固定模型，搜索策略映射并做减半周期稳健性分析
- `experiment-summary`
  - 汇总当前实验产物，形成总表

## 公共参数说明

### `--model`

机器学习模型：

- `ridge`
- `lasso`
- `svm`
- `rf`
- `lgbm`
- `xgboost`

深度学习模型：

- `lstm`
- `cnn_lstm`
- `gru`
- `tcn`

### `--task`

- `classification`
  - 方向预测，目标列是 `direction_h`
- `regression`
  - 幅度预测，目标列是 `log_ret_h`

### `--dataset-variant`

- `onchain`
  - 原始链上特征
- `ta`
  - 价格 / TA / 日历结构特征
- `all`
  - 全部特征
- `boruta_onchain`
  - 筛选后的链上特征
- `boruta_ta`
  - 筛选后的 TA / 时间结构特征
- `boruta_all`
  - 筛选后的全特征集
- `univariate`
  - 单变量价格基线

## 批量脚本

调参与主实验：

- [`scripts/run_core_experiments.ps1`](scripts/run_core_experiments.ps1)
- [`scripts/run_ml_tuning_full.ps1`](scripts/run_ml_tuning_full.ps1)
- [`scripts/run_dl_tuning_full.ps1`](scripts/run_dl_tuning_full.ps1)

减半周期 / 策略空间稳定性：

- [`scripts/run_ml_halving_strategy_full.ps1`](scripts/run_ml_halving_strategy_full.ps1)
- [`scripts/run_dl_halving_strategy_full.ps1`](scripts/run_dl_halving_strategy_full.ps1)

示例：

```powershell
.\scripts\run_ml_tuning_full.ps1 -Models rf,xgboost,lgbm -Trials 20
.\scripts\run_dl_halving_strategy_full.ps1 -Models 'lstm','cnn_lstm','gru','tcn' -Tasks 'classification','regression' -Variants 'boruta_onchain','onchain' -CostBps 5 -PredictionScope oos
```

## 输出目录

- `data/features/`
  - 特征集、预测结果、指标 JSON、回测产物
- `models_saved/`
  - 最终模型与元信息
- `reports/summary/`
  - 汇总表、调参结果、稳定性分析、最新预测
- `reports/figures/`
  - `Equity / Drawdown / Pred vs Actual` 图
- `reports/trading/`
  - 交互式交易图
- `reports/batch_runs/`
  - 批量实验日志

## 研究主线

当前最值得聚焦的问题是：

1. `boruta_onchain` 相对原始链上特征是否更稳定
2. 分类与回归信号，哪一种更容易转化为收益
3. `ML` 与 `DL` 在统一 `OOS` 和统一策略空间下谁更稳、谁上限更高

当前仓库里的结果已经表明：

- 分类任务通常是 `ML` 更稳
- 回归任务中，部分 `DL` 模型具有更高收益上限
- 不能只看 `F1 / RMSE`，还必须结合：
  - `cumulative return`
  - `Sharpe`
  - `max drawdown`
  - 成本敏感性
  - 分周期稳健性

## 文档入口

- [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md)
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
- [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md)
- [`docs/THESIS_NOTES.md`](docs/THESIS_NOTES.md)
- [`docs/REPO_LAYOUT.md`](docs/REPO_LAYOUT.md)

## 说明

- 本项目是 `paper-guided`，不是对参考论文的逐项严格复现
- 当前最强结果不代表所有市场周期都同样有效
- `test-full-history` 结果不能替代严格 `OOS`
- 深度学习模型对训练路径更敏感，解释结果时应结合稳健性分析
