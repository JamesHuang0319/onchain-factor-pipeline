# crypto_predict

基于链上数据的 BTC 收益预测研究项目。当前主线已经统一到单一配置驱动的研究流水线，支持数据下载、特征构建、特征筛选、时间序列训练、回测、报告生成和实验汇总。

## 当前状态
- 研究对象：`BTC-USD`
- 任务类型：`classification` 方向预测、`regression` 幅度预测
- 当前主力模型：`svm`、`rf`、`lgbm`、`xgboost`
- 已实现线性基线：`lasso`、`ridge`
- 已实现链上主源：`Coin Metrics Community API`
- 已保留兼容数据源：`Blockchain.com`
- 结果输出前缀：`btc_predict`

当前仓库重点是先跑通并比较 `ML` 主线。`DL` 相关配置已预留，但 `LSTM / TCN / CNN-LSTM / LSTNet` 还不是当前稳定主线。

## 核心配置
- `configs/experiment.yaml`
  主实验配置，控制任务、模型、数据集变体、特征筛选、回测与输出。
- `configs/data.yaml`
  数据源、时间范围、缓存目录、切分方式与标签设置。

## 数据与数据集变体
当前支持的特征族：
- `onchain`
- `ta`
- `all`
- `boruta_onchain`
- `boruta_ta`
- `boruta_all`
- `univariate`

`boruta_*` 不是标准 Boruta 复现，而是两阶段筛选：
1. Boruta-like RF 重要性过滤
2. Lasso / L1 二次收缩

## 已实现模型
- `svm`
  支持分类与回归
- `rf`
  支持分类与回归
- `lgbm`
  支持分类与回归
- `xgboost`
  支持分类与回归
- `lasso`
  当前用于回归
- `ridge`
  当前用于回归

说明：
- `xgboost` 属于树模型里的梯度提升方法，不是深度学习。
- `lgbm` 和 `xgboost` 现在已经是两个独立入口，不再混用。

## 最小运行流程
```bash
python -m src.cli download-data --config configs/experiment.yaml
python -m src.cli build-features --config configs/experiment.yaml
python -m src.cli data-audit --config configs/experiment.yaml --dataset-variant all
python -m src.cli validate --config configs/experiment.yaml
```

单组实验示例：
```bash
python -m src.cli train --config configs/experiment.yaml --model rf --task regression --dataset-variant boruta_all
python -m src.cli backtest --config configs/experiment.yaml --model rf --task regression --dataset-variant boruta_all
python -m src.cli report --config configs/experiment.yaml --model rf --task regression --dataset-variant boruta_all
```

最新样本预测：
```bash
python -m src.cli predict-latest --config configs/experiment.yaml --model svm --task classification --dataset-variant onchain
```

实验总表：
```bash
python -m src.cli experiment-summary --config configs/experiment.yaml --cost-bps 5
```

## 批量实验
核心 24 组实验：
- 模型：`svm / lgbm / rf`
- 任务：`classification / regression`
- 数据集：`onchain / all / boruta_onchain / boruta_all`

完整运行：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_core_experiments.ps1
```

只跑回测和报告：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_core_experiments.ps1 -SkipTrain
```

脚本会输出：
- 当前进度
- 已耗时
- 平均每组耗时
- 预计剩余时间
- 每组日志路径

## 主要输出
- `data/features/`
  特征集、预测结果、指标 JSON、回测敏感性 CSV、权益曲线
- `models_saved/`
  最终全样本模型和元信息
- `reports/00_summary/`
  汇总表、实验摘要、最新预测
- `reports/figures/`
  Equity、Drawdown、Pred vs Actual 图
- `reports/trading/`
  交互式交易图
- `reports/batch_runs/`
  批量实验日志和批次汇总

当前实验总表：
- `reports/00_summary/btc_predict_experiment_summary.csv`
- `reports/00_summary/btc_predict_experiment_summary.md`

## 当前研究主线
目前最重要的问题不是继续扩框架，而是持续回答这 3 个问题：
1. 链上因子是否相对纯价格/TA 带来增量价值
2. 方向预测和幅度预测谁更适合交易
3. 在当前数据与验证框架下，哪个模型最稳

建议顺序：
1. 先固定当前 `ML` 主线
2. 再扩额外链上因子
3. 再补 `DL` 基线

## 文档
- `docs/PROJECT_PLAN.md`
- `docs/DATA_FOUNDATION_PLAN.md`
- `docs/METHODOLOGY.md`
- `docs/EXPERIMENTS.md`
- `docs/THESIS_NOTES.md`
- `docs/REPO_LAYOUT.md`

## 说明
- 本项目当前是 `paper-guided`，不是对参考论文的严格逐项复现。
- 结果判断不能只看单一指标，应同时看：
  - 预测指标
  - 回测收益
  - 回撤
  - 稳定性
