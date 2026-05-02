# 实验命令说明

本文实验统一通过 `configs/experiment.yaml` 和 `configs/data.yaml` 管理参数，并通过 `python -m src.cli ...` 作为主入口执行。除特殊说明外，正式结果均应基于样本外预测输出，而不是单次验证集结果。

## 1. 数据准备

完整数据准备流程包括下载、特征构建、数据审计和泄漏校验。

```powershell
python -m src.cli download-data --config configs/experiment.yaml
python -m src.cli build-features --config configs/experiment.yaml
python -m src.cli data-audit --config configs/experiment.yaml --dataset-variant all
python -m src.cli validate --config configs/experiment.yaml
```

这些命令对应论文第 3 章的数据采集、预处理、标签构建和防泄漏设计。正式训练前应至少确认特征文件已生成，数据审计结果无明显异常，泄漏校验能够通过。

## 2. 单组模型实验

单组实验一般按照 `train → backtest → report` 顺序执行。示例：

```powershell
python -m src.cli train --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
python -m src.cli backtest --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
python -m src.cli report --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
```

其中 `train` 负责 walk-forward 样本外训练并保存预测结果，`backtest` 将预测结果映射为交易信号并计算收益指标，`report` 生成图表和 Markdown 摘要。

## 3. 超参数优化

超参数搜索使用随机搜索方式。示例：

```powershell
python -m src.cli tune --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain
```

查看模型搜索空间：

```powershell
python -m src.cli show-search-space --model rf --task classification
python -m src.cli show-search-space --model tcn --task regression
```

导出全部搜索空间：

```powershell
python -m src.cli show-search-space --out reports/summary/tuning_search_spaces.md
```

调优阶段用于确定模型参数，正式论文结果仍应以后续样本外训练、预测评价和回测结果为准。

## 4. 全矩阵安全补跑

当需要补齐所有模型、任务和数据集变体时，使用安全补跑脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_full_matrix_safe.ps1 -ContinueOnError
```

该脚本会扫描所有有效组合，并根据当前产物状态决定需要执行哪些步骤。

| 状态 | 含义 | 后续动作 |
| --- | --- | --- |
| `完整产物` | 预测、回测、报告均存在 | 跳过 |
| `缺预测` | 预测文件或指标文件缺失 | 执行 `train → backtest → report` |
| `缺回测` | 预测存在但回测产物缺失 | 执行 `backtest → report` |
| `缺报告` | 预测和回测存在但报告缺失 | 执行 `report` |

只扫描缺失情况、不执行实验：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_full_matrix_safe.ps1 -DryRun
```

## 5. Dashboard 监控

启动本地实验监控台：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\serve_experiment_dashboard.ps1
```

访问地址：

```text
http://127.0.0.1:8765/dashboard.html
```

Dashboard 读取 `reports/supplement_runs/latest_run_state.json` 和 `reports/supplement_runs/dashboard_data.json`，用于展示当前运行状态、任务矩阵、待补事项、日志和代表性结果排名。

如果只想重新生成 Dashboard 文件：

```powershell
python scripts\build_experiment_dashboard.py --refresh-seconds 5
```

## 6. 批量脚本

机器学习批量脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_ml_fixed_experiments.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_ml_tuning_full.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_ml_strategy_stability_full.ps1
```

深度学习批量脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_dl_fixed_experiments.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_dl_tuning_full.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_dl_strategy_stability_full.ps1
```

固定参数脚本主要执行 `train/backtest/report`，调参脚本用于随机搜索候选参数，策略稳定性脚本用于分阶段和不同交易映射规则下的稳健性检查。

## 7. 稳健性与策略映射

减半周期与策略空间分析示例：

```powershell
python -m src.cli halving-strategy-study --config configs/experiment.yaml --model rf --task classification --dataset-variant boruta_onchain --cost-bps 5 --prediction-scope oos
```

该命令用于检查预测信号在不同市场阶段和不同交易规则下的收益转化能力。论文第 6 章中的交易策略分析和稳健性分析主要依赖这类结果。

## 8. 实验汇总

刷新实验总表：

```powershell
python -m src.cli experiment-summary --config configs/experiment.yaml --cost-bps 5
```

生成的汇总结果主要位于 `reports/summary/`，可用于整理第 5 章预测结果表和第 6 章回测结果表。

## 9. 常用参数

| 参数 | 可选值 |
| --- | --- |
| `--task` | `classification`、`regression` |
| `--model` | `ridge`、`lasso`、`svm`、`rf`、`lgbm`、`xgboost`、`lstm`、`cnn_lstm`、`gru`、`tcn` |
| `--dataset-variant` | `onchain`、`ta`、`all`、`boruta_onchain`、`boruta_ta`、`boruta_all`、`univariate` |

注意：`ridge` 和 `lasso` 当前仅用于回归任务。深度学习模型会基于时间窗口构造序列输入，因此训练耗时通常高于传统机器学习模型。
