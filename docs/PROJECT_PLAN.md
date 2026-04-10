# Project Plan

## Purpose

本文件不再记录早期工程搭建路线，而是作为**基于当前已提交仓库状态**的下一阶段任务清单。  
默认起点是当前远程仓库已经提交的实验框架、脚本、报告结构和核心结果。

## Current Baseline

当前仓库已经具备：

- 统一 CLI 实验入口
- `ML / DL` 模型训练与调参
- `walk-forward OOS` 主实验
- 回测与报告生成
- `halving-strategy-study`
- `ML / DL` 批量脚本
- `reports/summary` 汇总体系

因此，接下来的工作重点不再是“补流程”，而是：

- 固定论文主线
- 压缩实验范围
- 完成论文正文所需的最终结果整理

## Next Tasks

### 1. Finalize paper-grade model set

目标：把正文保留模型固定下来，避免继续无限扩展。

建议保留：

- `ML classification`
  - `rf + classification + boruta_onchain`
  - `xgboost + classification + boruta_onchain`
- `ML regression`
  - `svm + regression + boruta_onchain`
  - `rf + regression + boruta_onchain`
- `DL focus`
  - `tcn + regression + boruta_onchain`
  - 可选补充：
    - `lstm + regression + boruta_onchain`
    - `tcn + classification + boruta_onchain`

输出：

- 一张最终正文模型清单
- 一张附录模型清单

### 2. Freeze result versions

目标：避免后续重训覆盖掉已经确认要写进论文的版本。

需要做：

- 确认每个正文模型当前保留的是哪一版结果
- 如有必要，将关键产物复制到稳定备份目录
- 在文档中记录：
  - `model`
  - `task`
  - `dataset_variant`
  - `prediction_scope`
  - `best strategy`

### 3. Build final summary tables

目标：生成论文可直接使用的总表，而不是继续看零散 CSV。

需要整理：

- `ML vs DL` 总表
- 分类主表
- 回归主表
- 分周期稳健性表
- 策略映射最优表

建议统一字段：

- `model`
- `task`
- `dataset_variant`
- `best_return`
- `best_sharpe`
- `best strategy`
- `prediction_start`
- `cycle_2016_2020`
- `cycle_2020_2024`
- `cycle_2024_end`

### 4. Finish thesis result writing

目标：把当前结果转成论文正文，而不是停留在命令行和 CSV。

优先完成：

- 实验设置
- 结果总表
- 结果分析
- 稳健性分析
- 讨论与局限性

### 5. Optional data expansion only if necessary

目标：只有在正文证据不足时，才补充新数据源。

优先级：

1. 小规模补充高价值链上指标
2. 不做大规模无约束扩展

不建议：

- 再大规模增加模型
- 为追单点收益继续反复重训
- 在没有明确假设下继续堆因子

## Not Recommended

当前不建议继续投入的方向：

- 扩大量级更大的 DL 搜索
- 为所有模型重复重训刷最好结果
- 扩很多低解释性的外部指标
- 把项目继续拉向纯工程化策略优化

## Completion Definition

这一阶段可以认为完成，当且仅当：

- 正文模型已固定
- 关键结果版本已冻结
- 汇总表已生成
- `README` 和 `docs` 已与当前状态一致
- 论文实验结果章节已有初稿
