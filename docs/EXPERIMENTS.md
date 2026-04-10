# Experiments

## 1. Unified Entry Points

所有正式实验统一通过以下配置和 CLI 入口驱动：

- `configs/experiment.yaml`
- `configs/data.yaml`
- `python -m src.cli ...`

不要再维护旧的分散配置文件或早期迭代命令。

## 2. Experiment Axes

### Task axis

- `classification`
- `regression`

### Model axis

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

### Dataset axis

- `onchain`
- `ta`
- `all`
- `boruta_onchain`
- `boruta_ta`
- `boruta_all`
- `univariate`

## 3. Core Experiment Types

### A. Data foundation

顺序：

1. `download-data`
2. `build-features`
3. `data-audit`
4. `validate`

目标：

- 确认时间对齐
- 确认标签与缺失处理
- 确认无明显泄漏风险

### B. Hyperparameter search

命令：

```bash
python -m src.cli tune --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
```

说明：

- `tune` 使用随机搜索
- 候选集来自：
  - `configs/experiment.yaml -> tuning.search_spaces`
  - 或 `src/cli.py` 的内建搜索空间
- 详细候选参数可通过：

```bash
python -m src.cli show-search-space --model rf --task classification
```

查看。

### C. OOS training

命令：

```bash
python -m src.cli train --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
```

说明：

- `train` 是正式的 `walk-forward OOS` 实验入口
- 后续 `backtest / report / halving-strategy-study` 默认都基于它生成的 `*_preds.parquet`

### D. Backtest and report

命令：

```bash
python -m src.cli backtest --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
python -m src.cli report --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
```

输出：

- 回测敏感性 CSV
- Equity / Drawdown / Pred vs Actual 图
- Markdown 摘要报告

### E. Full-history scoring

命令：

```bash
python -m src.cli test-full-history --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
```

说明：

- 用保存的最终模型对完整历史重新打分
- 适合做 sanity check 或对照
- 不能替代严格 `OOS`

### F. Halving / strategy stability study

命令：

```bash
python -m src.cli halving-strategy-study --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain --cost-bps 5 --prediction-scope oos
```

固定周期：

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`

固定策略空间：

- `long_only_sign`
- `long_only_band_{0.0025, 0.005, 0.01}`
- `full_exposure_sign`
- `sign_band_{0.0025, 0.005, 0.01}`
- `quantile_long_only_{0.05, 0.10, 0.20}`
- `quantile_ls_{0.05, 0.10, 0.20}`

用途：

- 检查收益是否只集中在单一周期
- 检查同一模型更适合哪种信号映射

## 4. Batch Scripts

### Tuning

- `scripts/run_ml_tuning_full.ps1`
- `scripts/run_dl_tuning_full.ps1`

### Stability / strategy

- `scripts/run_ml_halving_strategy_full.ps1`
- `scripts/run_dl_halving_strategy_full.ps1`

### Core experiment batch

- `scripts/run_core_experiments.ps1`

## 5. Output Location Standard

实验结果统一输出到：

- `data/features/`
- `models_saved/`
- `reports/summary/`
- `reports/summary/tuning/`
- `reports/summary/stability/`
- `reports/figures/`
- `reports/trading/`
- `reports/batch_runs/`

不再使用旧的 `reports/00_summary` 路径。

## 6. Result Table Contract

每个正式实验结果应能追踪到：

- `model`
- `task`
- `dataset_variant`
- `prediction_scope`
- `cost_bps`
- `best_return`
- `best_sharpe`
- `strategy`
- `prediction_start`
- 周期切分结果

## 7. Acceptance Checklist

正式可写入论文的结果，至少应满足：

- 泄漏检查通过
- 配置已固定
- 预测指标已导出
- 回测结果已导出
- 图表 / Markdown 摘要已生成
- `OOS` 与 `full_history` 没有被混淆
- 如结果依赖策略映射，已经做过固定策略空间比较
