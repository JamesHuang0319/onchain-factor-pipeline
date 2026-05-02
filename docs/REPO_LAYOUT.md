# 项目目录结构

本项目目录按照“配置、代码、脚本、数据产物、报告产物和论文文档”组织。正式实验应优先通过配置文件和 CLI 入口执行，避免在不同脚本中分散硬编码实验参数。

## 1. 顶层文件

```text
.
├── README.md
├── PROJECT_RULES.md
├── requirements.txt
├── configs/
├── src/
├── scripts/
├── tests/
├── data/
├── models_saved/
├── reports/
└── docs/
```

| 路径 | 说明 |
| --- | --- |
| `README.md` | 项目首页，说明研究目标、复现入口和主要文档 |
| `PROJECT_RULES.md` | 项目约束与协作规则 |
| `requirements.txt` | Python 依赖 |
| `configs/` | 数据、模型、特征和实验参数配置 |
| `src/` | 核心代码 |
| `scripts/` | 批量实验和 Dashboard 辅助脚本 |
| `tests/` | 单元测试与防泄漏测试 |
| `data/` | 原始数据、特征集和实验中间产物 |
| `models_saved/` | 保存后的最终模型 |
| `reports/` | 图表、报告和汇总表 |
| `docs/` | 实验说明、目录说明和论文写作笔记 |

## 2. 配置目录

| 路径 | 说明 |
| --- | --- |
| `configs/experiment.yaml` | 主实验配置，包含任务、模型、特征集、调参空间和输出路径 |
| `configs/data.yaml` | 数据源、样本区间、时间切分和下载设置 |

配置文件是复现实验的核心入口。研究对象、预测步长、数据集变体、模型参数和输出目录都应优先在配置文件中管理。

## 3. 源代码目录

```text
src/
├── cli.py
├── ingest/
├── datasets/
├── features/
├── models/
├── evaluation/
└── backtest/
```

| 路径 | 说明 |
| --- | --- |
| `src/cli.py` | 命令行主入口，封装数据准备、训练、回测、报告和汇总命令 |
| `src/ingest/` | 价格数据、链上数据下载和缓存逻辑 |
| `src/datasets/` | 数据合并、标签构建和数据集变体处理 |
| `src/features/` | 价格技术面特征、链上衍生特征和周期特征构造 |
| `src/models/` | 机器学习与深度学习模型实现 |
| `src/evaluation/` | walk-forward 验证、预测指标和 IC 诊断 |
| `src/backtest/` | 交易信号映射、收益计算和回测指标 |

## 4. 脚本目录

| 脚本 | 用途 |
| --- | --- |
| `scripts/run_ml_fixed_experiments.ps1` | 机器学习固定参数批量实验 |
| `scripts/run_dl_fixed_experiments.ps1` | 深度学习固定参数批量实验 |
| `scripts/run_ml_tuning_full.ps1` | 机器学习批量调参 |
| `scripts/run_dl_tuning_full.ps1` | 深度学习批量调参 |
| `scripts/run_ml_strategy_stability_full.ps1` | 机器学习策略映射与稳健性批量分析 |
| `scripts/run_dl_strategy_stability_full.ps1` | 深度学习策略映射与稳健性批量分析 |
| `scripts/run_full_matrix_safe.ps1` | 全矩阵安全补跑，自动跳过已有完整结果 |
| `scripts/build_experiment_dashboard.py` | 生成实验 Dashboard 和 JSON 数据 |
| `scripts/serve_experiment_dashboard.ps1` | 启动本地 Dashboard 服务 |
| `scripts/watch_experiment_dashboard.ps1` | 定时刷新 Dashboard 数据 |

## 5. 数据与模型产物

| 路径 | 说明 |
| --- | --- |
| `data/raw/` | 原始价格数据和链上数据缓存 |
| `data/features/` | 特征集、预测结果、指标 JSON、回测敏感性结果和净值序列 |
| `models_saved/` | 保存后的模型文件与元信息 |

`data/features/` 是连接第 5 章和第 6 章结果分析的关键目录。预测指标、回测结果和样本外预测文件通常都可以在这里追踪到。

## 6. 报告目录

```text
reports/
├── summary/
├── experiments/
├── supplement_runs/
├── demos/
└── batch_runs/
```

| 路径 | 说明 |
| --- | --- |
| `reports/summary/` | 汇总表、调参记录、稳健性分析和论文候选表格 |
| `reports/experiments/figures/` | 净值曲线、回撤曲线、预测对比图等 PDF 图表 |
| `reports/experiments/trading/` | 交互式交易图 |
| `reports/experiments/summaries/` | 单组实验 Markdown 摘要 |
| `reports/supplement_runs/` | 全矩阵补跑日志、批次摘要和 Dashboard 文件 |
| `reports/demos/` | 演示或展示用途的结果副本 |
| `reports/batch_runs/` | 批量实验运行日志 |

## 7. 论文文件与本地材料

项目根目录中可能包含论文初稿、学校模板和本地参考资料，例如：

```text
黄名靖_毕业论文.docx
中南大学毕业论文模版.docx
论文.pdf
论文2.pdf
```

这些文件主要服务于本地写作，不属于模型流水线的核心代码产物。若需要提交代码仓库，应根据实际要求决定是否纳入版本控制。

## 8. 推荐阅读顺序

第一次进入项目时，建议按以下顺序阅读：

1. `README.md`
2. `configs/experiment.yaml`
3. `docs/EXPERIMENTS.md`
4. `src/cli.py`
5. `docs/THESIS_NOTES.md`

论文写作阶段，建议优先关注：

1. `reports/summary/`
2. `reports/experiments/`
3. `reports/supplement_runs/dashboard.html`
4. `docs/THESIS_NOTES.md`
