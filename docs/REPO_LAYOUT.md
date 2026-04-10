# Repo Layout

## Top Level

- `README.md`
  - 项目入口，说明常用命令、公共参数和主要输出目录。
- `PROJECT_RULES.md`
  - 仓库级规则与约束。
- `requirements.txt`
  - Python 依赖列表。
- `论文.pdf`, `论文2.pdf`
  - 本地参考论文，不属于流水线生成产物。

## Source Code

- `src/`
  - 主要代码目录。
- `src/cli.py`
  - 命令行主入口，包含数据准备、训练、回测、报告、汇总和稳健性分析命令。
- `src/ingest/`
  - 数据下载与缓存逻辑。
- `src/datasets/`
  - 数据集构建、标签生成、特征集变体处理。
- `src/features/`
  - 价格、TA、链上因子构造逻辑。
- `src/models/`
  - `ML / DL` 模型实现。
- `src/evaluation/`
  - 指标计算、IC 诊断、walk-forward 评估。
- `src/backtest/`
  - 信号映射与回测逻辑。

## Configuration

- `configs/experiment.yaml`
  - 主实验配置。
  - 包含模型默认参数、调参搜索空间、任务与特征集设置。
- `configs/data.yaml`
  - 数据源、时间范围、切分规则和输出目录配置。

## Tests

- `tests/`
  - 单元测试与时序泄漏检查。
- `tests/test_no_leakage.py`
  - 当前最重要的安全性测试之一。

## Scripts

- `scripts/run_ml_fixed_experiments.ps1`
  - `ML` 固定参数批量 `train/backtest/report` 脚本。
- `scripts/run_dl_fixed_experiments.ps1`
  - `DL` 固定参数批量 `train/backtest/report` 脚本。
- `scripts/run_ml_tuning_full.ps1`
  - `ML` 批量调参脚本。
- `scripts/run_dl_tuning_full.ps1`
  - `DL` 批量调参脚本。
- `scripts/run_ml_strategy_stability_full.ps1`
  - `ML` 固定策略空间 + 分周期稳健性批量脚本。
- `scripts/run_dl_strategy_stability_full.ps1`
  - `DL` 固定策略空间 + 分周期稳健性批量脚本。

## Generated Artifacts

- `data/raw/`
  - 原始价格与链上数据缓存。
- `data/features/`
  - 特征集、预测结果、指标 JSON、回测结果等中间产物。
- `models_saved/`
  - 最终模型与元信息。
- `reports/`
  - 所有图表、汇总表和实验报告。

## Reports Layout

- `reports/summary/`
  - 汇总结果主目录。
- `reports/summary/model_selection/`
  - `ML / DL` 对比、模型筛选与统一汇总表。
- `reports/summary/final_tables/`
  - 最终论文倾向使用的总表与综合摘要。
- `reports/summary/tuning/`
  - 随机搜索 trial 记录与 best 参数。
- `reports/summary/stability/`
  - `halving-strategy-study`、分周期稳健性与策略搜索结果。
- `reports/summary/diagnostics/`
  - IC 诊断与相关辅助表。
- `reports/summary/latest_predictions/`
  - 最新样本预测摘要。
- `reports/summary/data_audit/`
  - 数据审计结果。
- `reports/experiments/`
  - 正式实验输出。
- `reports/experiments/figures/`
  - PDF 图表，如 `equity / drawdown / pred_vs_actual`。
- `reports/experiments/trading/`
  - 交互式 HTML 交易图。
- `reports/experiments/summaries/`
  - 单模型正式 Markdown 报告。
- `reports/demos/`
  - 演示 / 录视频专用副本。
- `reports/demos/figures/`
  - 演示用 PDF 图。
- `reports/demos/trading/`
  - 演示用 HTML 图。
- `reports/demos/summaries/`
  - 演示用 Markdown 报告。
- `reports/batch_runs/`
  - 批量实验日志。

## Backup / Local Only

- `artifacts_backup/`
  - 本地备份目录，用于重训前保存旧产物，通常不提交。

## Practical Reading Order

如果是第一次进入仓库，建议按这个顺序看：

1. `README.md`
2. `configs/experiment.yaml`
3. `src/cli.py`
4. `docs/EXPERIMENTS.md`
5. `reports/summary/`

如果是论文写作阶段，建议优先关注：

1. `reports/summary/btc_predict_experiment_summary.md`
2. `reports/summary/stability/`
3. `docs/METHODOLOGY.md`
4. `docs/THESIS_NOTES.md`
