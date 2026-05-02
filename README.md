# 基于链上数据的比特币收益预测研究

本仓库为本科毕业论文“基于链上数据的加密货币收益预测模型研究”的实验项目。项目围绕比特币日频收益预测问题，构建了从多源数据采集、特征工程、样本外预测到交易回测的完整研究流水线，用于检验链上数据在统计预测和经济价值两个层面是否具有增量作用。

项目并不是面向实盘交易的策略系统，而是服务于论文研究的可复现实验框架。所有正式实验均围绕统一的数据边界、特征版本、模型集合和样本外验证规则展开，以保证不同模型和不同信息结构之间具有一致的比较基础。

## 研究设计

| 维度 | 设定 |
| --- | --- |
| 研究对象 | `BTC-USD` |
| 数据频率 | 日频 |
| 价格数据 | Yahoo Finance |
| 链上数据 | Coin Metrics Community API，兼容 Blockchain.com |
| 分类任务 | 预测次日涨跌方向 `direction_h` |
| 回归任务 | 预测次日对数收益率 `log_ret_h` |
| 验证方式 | 时间序列样本外验证，采用 walk-forward 划分 |

特征体系包括价格与技术面特征、链上衍生特征以及比特币减半周期特征。为比较不同信息来源的作用，实验进一步构造了 `onchain`、`ta`、`all`、`boruta_onchain`、`boruta_ta`、`boruta_all` 和 `univariate` 等数据集变体。

## 方法框架

整体实验流程可以概括为：

```text
数据采集 → 清洗对齐 → 特征工程 → 特征筛选 → 模型训练 → 样本外预测 → 交易回测 → 结果汇总
```

模型体系分为机器学习模型和深度学习模型两类。机器学习模型包括 `Ridge`、`Lasso`、`SVM/SVR`、`Random Forest`、`LightGBM` 和 `XGBoost`；深度学习模型包括 `LSTM`、`CNN-LSTM`、`GRU` 和 `TCN`。不同模型共享同一批基础特征来源，但深度学习模型会进一步基于时间窗口重构序列输入。

## 快速复现

安装依赖后，先完成数据与特征准备：

```powershell
python -m src.cli download-data --config configs/experiment.yaml
python -m src.cli build-features --config configs/experiment.yaml
python -m src.cli data-audit --config configs/experiment.yaml --dataset-variant all
python -m src.cli validate --config configs/experiment.yaml
```

单组实验按照 `train → backtest → report` 的顺序执行：

```powershell
python -m src.cli train --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
python -m src.cli backtest --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
python -m src.cli report --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
```

若需要补齐全部模型、任务和数据集变体的实验产物，可运行安全补跑脚本。该脚本会自动跳过已有完整结果，只补缺失的预测、回测或报告。

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_full_matrix_safe.ps1 -ContinueOnError
```

更多实验命令见 [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)。

## 实验监控

项目提供本地 Dashboard 用于查看实验进度、产物完整度、任务矩阵和代表性结果排名。

```powershell
powershell -ExecutionPolicy Bypass -File scripts\serve_experiment_dashboard.ps1
```

启动后访问：

```text
http://127.0.0.1:8765/dashboard.html
```

Dashboard 主要用于辅助实验补跑和结果检查，不作为论文正文结果来源。论文中使用的正式结果应以 `reports/summary/`、`reports/experiments/` 和最终整理后的表格为准。

## 输出与论文对应关系

| 论文部分 | 对应项目内容 |
| --- | --- |
| 第 3 章 数据来源与研究设计 | `src/ingest/`、`src/features/`、`src/datasets/`、`configs/` |
| 第 4 章 预测模型构建与实验实现 | `src/models/`、`src/evaluation/`、`src/cli.py` |
| 第 5 章 预测结果分析 | `data/features/*_metrics.json`、`reports/summary/` |
| 第 6 章 交易策略与经济价值分析 | `data/features/*_backtest_sensitivity.csv`、`reports/experiments/` |
| 第 7 章 结论与展望 | 第 5、6 章结果汇总与局限性讨论 |

主要输出目录包括：

- `data/features/`：特征集、样本外预测、预测指标和回测中间产物。
- `models_saved/`：最终模型与模型元信息。
- `reports/summary/`：实验汇总表、调参记录、稳健性分析和论文候选表格。
- `reports/experiments/`：单组实验图表、交易图和 Markdown 摘要。
- `reports/supplement_runs/`：全矩阵补跑日志、批次摘要和本地 Dashboard 文件。

更完整的目录说明见 [docs/REPO_LAYOUT.md](docs/REPO_LAYOUT.md)。

## 文档入口

- [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)：实验命令与批量运行说明。
- [docs/REPO_LAYOUT.md](docs/REPO_LAYOUT.md)：项目目录与产物结构。
- [docs/THESIS_NOTES.md](docs/THESIS_NOTES.md)：论文写作提示、结果组织和风险说明。
- [docs/METHODOLOGY.md](docs/METHODOLOGY.md)：方法设计与实验规范说明。

## 说明

本项目用于学术研究和论文写作，不构成任何投资建议。由于链上数据覆盖、模型训练路径和市场阶段差异均可能影响实验结果，最终结论应以样本外预测、回测表现和稳健性分析的综合结果为依据。
