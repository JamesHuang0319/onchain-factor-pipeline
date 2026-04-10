# Thesis Notes

## 1. Thesis Positioning

毕业论文定位：

- 主题：基于链上数据的加密货币收益预测模型研究
- 对象：`BTC-USD`
- 目标：同时检验统计有效性与交易有效性

论文不应只回答“哪个模型指标最高”，而应回答：

- 链上因子是否真正带来增量价值
- 不同预测任务是否导向不同最优模型
- 预测结果是否能稳定转化为经济价值

## 2. Core Claims to Validate

当前最值得验证的核心命题应当是：

1. 筛选后的链上特征相对原始链上特征和价格/TA 基线具有更稳定的增量价值。
2. 分类任务与回归任务可能导向不同的最优模型与交易映射。
3. 模型表现具有显著的市场阶段依赖性，因此必须结合分周期稳健性分析。
4. 预测指标最优、方向指标最优与收益最优不一定一致。

注意：

- 不再预设“方向任务一定比幅度任务更适合交易”
- 结论应以当前真实实验结果为准，而不是先入为主

## 3. Recommended Narrative

当前论文叙事更适合这样组织：

### 主线

- 经济价值 / 交易收益
- 重点比较：
  - `cumulative return`
  - `Sharpe`
  - `max drawdown`
  - 成本敏感性

### 副线

- 方向预测
- 用于解释：
  - 分类信号是否有交易意义
  - 为什么分类最优模型不一定等于收益最优模型

### 特征主线

- `boruta_onchain`
  - 作为论文最核心的特征版本

## 4. Result Writing Template

每组正文结果建议按固定模板写：

1. 数据范围
- 资产
- 日期区间
- 特征集版本

2. 实验设置
- 任务类型
- 模型
- `walk-forward` 设定
- 成本设定

3. 预测结果
- 分类：`Accuracy / F1 / MCC / balanced accuracy`
- 回归：`RMSE / MAE / R2 / IC`

4. 交易结果
- `cumulative return`
- `Sharpe`
- `max drawdown`
- `turnover`

5. 解释
- 为什么这个模型有效
- 它在哪些周期有效
- 它的局限是什么

## 5. Figure and Table Mapping

建议正文保留的图表类型：

### 预测比较表

- `task × model × dataset_variant`

### 经济价值主表

- `best_return`
- `best_sharpe`
- `best strategy`
- `prediction_start`

### 稳健性表

- `full_sample`
- `2016-07-09 ~ 2020-05-10`
- `2020-05-11 ~ 2024-04-19`
- `2024-04-20 ~ end`

### 图形

- `equity curve`
- `drawdown`
- 必要时可补 `pred vs actual`

## 6. Model Presentation Strategy

正文不应把所有模型都展开。  
应只保留少量代表模型。

当前更合适的结构是：

### ML classification

- `rf + classification + boruta_onchain`
- `xgboost + classification + boruta_onchain`

### ML regression

- `svm + regression + boruta_onchain`
- `rf + regression + boruta_onchain`

### DL focus

- `tcn + regression + boruta_onchain`
- 可选补充：
  - `lstm + regression + boruta_onchain`
  - `tcn + classification + boruta_onchain`

## 7. Risks to Discuss

正文和答辩里必须主动讨论这些风险：

- 市场阶段依赖
- 深度学习训练路径敏感性
- 特征扩张导致过拟合
- 免费数据源覆盖限制
- 回测假设仍有简化
  - 例如没有完整建模做空融资成本与更细粒度滑点

## 8. Final Conclusion Style

结论部分应避免：

- 只按单一指标宣布“最优模型”
- 把单次最好结果写成绝对稳定结论

更稳的写法应强调：

- 统计指标与经济价值并不总是一致
- `ML` 与 `DL` 在不同任务上各有优势
- 链上因子的价值需要结合特征筛选与稳健性分析理解
- 最终结论应体现：
  - 准确性
  - 稳定性
  - 可解释性
  - 可复现性
