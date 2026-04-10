# Methodology

## 1. Problem Definition

本项目研究比特币单资产日频预测，目标是比较链上数据在两类任务中的作用：

- `classification`
  - 预测次日涨跌方向 `direction_h`
- `regression`
  - 预测次日对数收益率 `log_ret_h`

项目不只比较统计指标，还比较预测信号能否转化为交易收益。

## 2. Data Scope

- 资产：`BTC-USD`
- 频率：`1D`
- 价格数据：`Yahoo Finance`
- 主链上数据源：`Coin Metrics Community API`
- 兼容链上数据源：`Blockchain.com`

时间范围由 `configs/data.yaml` 中的价格配置统一控制。

## 3. Feature Blocks

当前特征按语义可分为三类：

- 价格 / 市场特征
  - OHLCV 派生因子
- TA / 时间结构特征
  - 技术指标、滚动统计、日历结构特征
- 链上特征
  - 交易活跃度、地址活跃度、费用、哈希率、供给、市值及其派生变化率/标准化特征

此外，当前数据集还加入了减半周期背景特征：

- `halving_cycle_id`
- `halving_days_since_prev`
- `halving_days_to_next`
- `halving_progress`

这些特征是基于日历与减半锚点构造的事件/周期特征，不属于纯链上观测因子。

## 4. Dataset Variants

项目统一维护以下特征集变体：

- `onchain`
- `ta`
- `all`
- `boruta_onchain`
- `boruta_ta`
- `boruta_all`
- `univariate`

其中：

- `boruta_*`
  - 表示经过筛选后的特征子集
- `univariate`
  - 表示单变量价格基线

## 5. Labels

- 回归标签：
  - `log_ret_h = log(close[t+h] / close[t])`
- 分类标签：
  - `direction_h = 1 if log_ret_h > 0 else 0`

当前主要研究的是 `h = 1` 的次日预测。  
相关配置同时受：

- `configs/data.yaml -> prediction.horizon`
- `configs/experiment.yaml -> label_horizon_days`

控制。

## 6. Preprocessing Rules

- 所有特征块按价格日历对齐
- 缺失值按配置策略处理
- 始终保留时间顺序
- 先按时间切分，再做标准化
- 不允许在全样本上先 fit 再 split

这套规则的目标是避免时序任务中常见的数据泄漏。

## 7. Leakage Guards

正式实验前必须满足：

- 特征在时间 `t` 只能使用 `t` 及之前的信息
- 滚动指标必须是向后看的
- 链上数据只允许合理的前向填充
- `tests/test_no_leakage.py` 必须通过

## 8. Feature Selection

当前筛选流程不是标准 Boruta 的逐项复现，而是更偏工程化、可复现的两阶段方案：

1. `Boruta-like RF importance` 预筛选
2. `Lasso / Logistic-L1` 再筛选

其中：

- 回归任务使用 `Lasso`
- 分类任务使用 `LogisticRegression(L1)`

最终形成：

- `boruta_onchain`
- `boruta_ta`
- `boruta_all`

这三类主筛选数据集。

## 9. Model Families

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

输入形状：

- `ML`
  - `(samples, features)`
- `DL`
  - `(samples, timesteps, features)`

深度学习窗口长度不是固定常数，会随模型默认参数和调优结果变化，不应再简单写成单一 `timesteps = 5`。

## 10. Training and Validation

主实验采用时间序列 `walk-forward` 评估：

- `train_years = 3`
- `val_months = 6`
- `test_months = 6`
- `step_months = 3`
- `walk_forward_type = expanding`

也就是说：

- 训练窗口逐步扩张
- 验证和测试窗口按时间向前滚动
- 这是当前正式 `OOS` 结果的基础

另外：

- `tune`
  - 使用单个 chronological validation split 做随机搜索
- `train`
  - 产生正式 `walk-forward OOS` 预测
- `test-full-history`
  - 用保存的最终模型对完整历史重新打分
  - 不能替代严格 `OOS`

## 11. Predictive Evaluation

分类任务主要看：

- `Accuracy`
- `Precision`
- `Recall`
- `F1`

回归任务主要看：

- `RMSE`
- `MAE`
- `R2`

补充指标：

- `directional accuracy`
- `IC / RankIC`

## 12. Backtest Mapping

项目将预测值映射为交易信号，再计算经济价值。

当前主要用到两层回测分析：

### A. 默认回测

- 基于 `train/backtest/report` 主流程
- 用统一交易规则形成基线结果

### B. 固定策略空间搜索

通过 `halving-strategy-study`，在固定模型预测不变的前提下，比较：

- `long_only_sign`
- `long_only_band`
- `full_exposure_sign`
- `sign_band`
- `quantile_long_only`
- `quantile_ls`

这一步用于回答：

- 同一模型更适合哪种信号映射
- 收益是否来自模型本身，还是主要来自策略暴露方式

## 13. Stability Analysis

稳健性分析当前主要包括：

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`

该分段基于 BTC 减半周期，用于刻画不同市场阶段下的有效性差异。  
它是评估层分段，不是训练切分规则。

## 14. Interpretation Principle

最终模型选择不能只看单一指标。  
应同时考虑：

- 预测误差 / 分类指标
- 收益水平
- `Sharpe`
- `max drawdown`
- 成本敏感性
- 分周期稳定性

因此，统计最优模型、方向最优模型和收益最优模型可能不是同一个。
