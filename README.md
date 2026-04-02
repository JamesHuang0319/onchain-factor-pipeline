# crypto_predict

加密货币收益预测与回测研究项目（毕业设计）。

当前项目已切换为统一配置驱动，不再使用旧的迭代配置文件。

## Core Configs
- `configs/data.yaml`: 数据源、时间范围、切分与目标字段
- `configs/experiment.yaml`: 主实验配置（任务、数据集变体、模型、回测、评估）

## Quick Start
```bash
python -m src.cli download-data --config configs/experiment.yaml
python -m src.cli build-features --config configs/experiment.yaml
python -m src.cli data-audit --config configs/experiment.yaml --dataset-variant all
python -m src.cli train --config configs/experiment.yaml --model lgbm
python -m src.cli backtest --config configs/experiment.yaml --model lgbm
python -m src.cli report --config configs/experiment.yaml --model lgbm
python -m src.cli validate --config configs/experiment.yaml

# Example: classification + on-chain variant
python -m src.cli train --config configs/experiment.yaml --model lgbm --task classification --dataset-variant onchain
python -m src.cli backtest --config configs/experiment.yaml --model lgbm --task classification --dataset-variant onchain
python -m src.cli report --config configs/experiment.yaml --model lgbm --task classification --dataset-variant onchain
```

批量跑核心 24 组实验（`svm/lgbm/rf x classification/regression x onchain/all/boruta_onchain/boruta_all`）：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_core_experiments.ps1
```

可用模型（当前已实现）：
- `svm`（分类/回归）
- `rf`（分类/回归）
- `lgbm`（分类/回归）
- `lasso`（回归）
- `ridge`（回归）

`boruta_*` 数据集默认使用两阶段特征提取：
1. Boruta（RF 重要性筛选）
2. Lasso/L1 二次收缩

你可以：
- 命令行显式指定 `--model`
- 或在 `configs/experiment.yaml -> decision.selected_model` 里指定默认模型

## Current Research Direction
1. 任务对比：方向分类 vs 幅度回归
2. 模型对比：ML vs DL
3. 数据集对比：7类数据版本（onchain/ta/all/boruta*/univariate）
4. 结果判定：预测指标 + 回测收益联合评估

## Docs
- 总体转型计划：`docs/PROJECT_PLAN.md`
- 数据基础规划：`docs/DATA_FOUNDATION_PLAN.md`
- 方法说明：`docs/METHODOLOGY.md`
- 实验规范：`docs/EXPERIMENTS.md`
- 论文写作笔记：`docs/THESIS_NOTES.md`
- 仓库布局规则：`docs/REPO_LAYOUT.md`
- 实验输出目录：`reports/`
