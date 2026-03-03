# crypto_predict

> 加密货币价格预测与回测闭环系统（毕业论文项目）  
> End-to-end crypto prediction & backtesting pipeline — price-only → on-chain → macro

---

## 📁 目录结构

```
crypto_predict/
├── configs/
│   ├── data.yaml                       # 数据源全局配置
│   ├── experiment_price_only.yaml      # Iter-0: 纯价格因子
│   └── experiment_price_onchain.yaml   # Iter-1: 价格+链上因子
├── src/
│   ├── ingest/        price.py · onchain.py
│   ├── etl/           cleaner.py
│   ├── features/      price_factors.py · onchain_factors.py · macro_factors.py
│   ├── datasets/      build_dataset.py  ← 防泄漏断言在此
│   ├── models/        base.py · ridge.py · lgbm.py
│   ├── evaluation/    metrics.py · walk_forward.py
│   ├── backtest/      strategy.py · backtester.py
│   ├── visualization/ matplotlib_reports.py · plotly_trading_chart.py
│   └── cli.py         ← 所有命令入口
├── data/
│   ├── raw/{yfinance,blockchain}/      缓存目录
│   ├── processed/
│   └── features/
├── reports/
│   ├── figures/        *.pdf 论文静态图
│   ├── trading/        *.html Plotly交互图
│   └── summary.md
├── tests/
│   └── test_no_leakage.py
└── requirements.txt
```

---

## ⚡ 环境安装

```bash
# 1. 创建 conda 环境（推荐 Python 3.11）
conda create -n crypto_predict python=3.11 -y
conda activate crypto_predict

# 2. 安装依赖
pip install -r requirements.txt
```

---

## 🚀 3 条命令快速 Demo（Iter-0 price-only）

```bash
# 第 1 条：下载数据 + 构建特征 + 训练模型（打通整个 pipeline）
python -m src.cli train --config configs/experiment_price_only.yaml

# 第 2 条：回测（打印绩效表，保存权益曲线）
python -m src.cli backtest --config configs/experiment_price_only.yaml

# 第 3 条：生成报告（PDF 静态图 + Plotly 交互式 K 线图 + summary.md）
python -m src.cli report --config configs/experiment_price_only.yaml
```

运行完毕后：
- `reports/trading/*.html`  — 交互式 K 线+预测+买卖点图（浏览器打开）
- `reports/figures/*.pdf`   — 论文用静态图
- `reports/summary.md`      — 汇总报告

---

## 📋 完整命令列表

```bash
# 1. 仅下载数据（有缓存跳过网络）
python -m src.cli download-data --config configs/experiment_price_only.yaml

# 2. 仅构建特征（输出 data/features/*.parquet）
python -m src.cli build-features --config configs/experiment_price_only.yaml

# 3. 训练（walk-forward，输出预测 + 指标 JSON）
python -m src.cli train --config configs/experiment_price_only.yaml --model lgbm
python -m src.cli train --config configs/experiment_price_only.yaml --model ridge

# 4. 回测（费率敏感性分析 5/10/20 bps）
python -m src.cli backtest --config configs/experiment_price_only.yaml --model lgbm

# 5. 生成报告
python -m src.cli report --config configs/experiment_price_only.yaml --model lgbm

# 6. 防泄漏校验（CI/CD 必跑，非零退出码表示违规）
python -m src.cli validate --config configs/experiment_price_only.yaml

# 7. 单元测试（含泄漏检测）
pytest tests/test_no_leakage.py -v

# ── Iter-1: 加入链上因子 ──
python -m src.cli train --config configs/experiment_price_onchain.yaml --model lgbm
python -m src.cli backtest --config configs/experiment_price_onchain.yaml
python -m src.cli report --config configs/experiment_price_onchain.yaml
```

---

## 🔁 迭代路线 & 验证点

### Iter-0：纯价格因子 baseline（✅ 当前已实现）

| 步骤 | 可交付物 | 验证点 |
|------|---------|--------|
| 数据下载 | `data/raw/yfinance/BTC_USD.csv` | 行数 > 2000, 无 NaN close |
| 特征构建 | `data/features/iter0_*.parquet` | 20+ 特征列, 最后 7 行 label=NaN |
| 防泄漏 | `validate` 命令通过 | assert_no_leakage ✓ |
| 训练 | `*_preds.parquet` + `*_metrics.json` | RankIC > 0 (优于随机) |
| 回测 | 绩效表打印到终端 | Sharpe 有意义, 最大回撤 < 100% |
| 报告 | `reports/trading/*.html` | 浏览器可打开，K线+预测线可见 |

### Iter-1：+ 链上因子（✅ 当前已实现）

| 步骤 | 可交付物 | 验证点 |
|------|---------|--------|
| 链上下载 | `data/raw/blockchain/*.csv` | 4 个指标文件, 时间戳正确 |
| 特征构建 | 含链上列的 parquet | 特征数量 > 30 |
| 防泄漏 | 链上 ffill 只往前填充 | `test_ffill_direction` passed |
| 训练对比 | Iter-0 vs Iter-1 RankIC | 链上因子应提升 IC |

### Iter-2：+ 宏观因子（🚧 占位已实现，真实数据待接入）

使用 `macro_factors.py` 中 `use_dummy=True` 可跑通 pipeline，
Iter-2 真实实现见下文"下一步扩展"。

---

## ⚙️ 核心设计说明

### 防泄漏（Anti-Leakage）

| 规则 | 实现位置 |
|------|---------|
| Label 用 `shift(-7)` 生成 | `build_dataset.py` 第 88 行 |
| 特征只用 `t` 及之前数据 | `price_factors.py` 全部 rolling 向后 |
| 链上 ffill only（禁止 bfill）| `cleaner.py: clean_onchain()` |
| 宏观 `release_lag_days` 移位 | `macro_factors.py` TODO 注释 |
| 断言校验 | `assert_no_leakage()` + `pytest` |

### 模型 Fallback 链

```
LightGBM  →  XGBoost  →  sklearn HGBR
```
在 `lgbm.py` `_build_gbm()` 中自动检测可用后端。

### Walk-Forward CV

```
默认: train=3y, val=6m, test=6m, step=3m (expanding window)
不足 500 行: 自动退回 70/30 chronological split
```

---

## 🔭 下一步迭代建议

### 1. 加入 SOL-USD

修改 `configs/data.yaml`:
```yaml
price:
  symbols: ["BTC-USD", "ETH-USD", "SOL-USD"]
```
在 `build-features` 时循环 `symbols`，或将多资产 cross-section 传入
`long_short_signal()` 做横截面排名策略。

### 2. 接入宏观真实数据（Iter-2）

```bash
pip install fredapi
export FRED_API_KEY="your_key_here"
```

在 `macro_factors.py` 取消注释 FRED 代码块，
将 `data.yaml` 中 `macro.use_dummy` 改为 `false`。
关键：**必须** 保留 `shift(release_lag_days)` 防止公告日泄漏。

### 3. 接入 Gemini 文本因子（可选）

```
src/ingest/news.py       # 爬取/订阅新闻标题
src/ingest/gemini_llm.py # Gemini API → 情绪分数 / 关键词
src/features/nlp_factors.py # 将结构化情绪对齐到日期
```

在 `build_dataset.py` 中添加 `use_nlp=True` 分支，
与价格/链上因子合并后进统一的 `assert_no_leakage()` 检查。

---

## 📦 依赖版本

见 `requirements.txt`。核心：
- `yfinance >= 0.2.36`
- `lightgbm >= 4.3` (fallback: xgboost / sklearn)
- `plotly >= 5.20`
- `click >= 8.1`
- `pytest >= 8.0`
