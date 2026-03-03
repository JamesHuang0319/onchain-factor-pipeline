# Research Plan V1 (Locked Scope)

## Scope Lock
- V1 data sources are strictly limited to:
  - `yfinance` (price)
  - `Blockchain.com charts/stats` (on-chain, BTC-focused)
  - macro dummy factors (`macro.use_dummy=true`)
- Hard rule: **No new external data source is allowed until Iter-1D is complete**.
- Explicitly prohibited in V1:
  - `FRED`
  - `Glassnode`
  - `CoinMetrics`
  - `Deribit`
- `docs/deep-research-report.md` is reference-only for background/factor taxonomy/V2 roadmap, not for V1 source expansion.

---

## Read Summary (Requested Files)

### README.md
- Current pipeline is end-to-end and runnable through `src.cli`: download, feature build, train, backtest, report, validate.
- Iter-0 and Iter-1 baselines are already described; Iter-2 macro real-data is explicitly marked as future work.
- Existing output conventions already include `reports/figures/*.pdf`, `reports/trading/*.html`, and summary artifacts.

### PROJECT_RULES.md
- Non-negotiables: anti-leakage, walk-forward only, same split for comparisons, cache-first data discipline.
- Per-step engineering discipline: each step should touch only 1-3 files, then run smoke + pytest + metric delta check.
- Repo convention aligns with V1 controlled iteration (no uncontrolled feature expansion).

### docs/deep-research-report.md
- Valuable as research background and factor universe reference.
- Mentions many potential external sources (FRED, Glassnode, CoinMetrics, Deribit, etc.), which are treated as V2 optional only.
- Confirms strong emphasis on availability-time alignment and leakage control, consistent with V1 constraints.

---

# V1 Iteration Plan

---

## Iter-1A: Blockchain On-chain Ingestion Expansion (Within Locked Sources)

- Goal:
  - Extend Blockchain.com charts ingestion.
  - Add stable BTC on-chain metrics (e.g. fees, hashrate, difficulty, mempool, miner revenue).
  - No new external source allowed.

- Input:
  - `src/ingest/onchain.py`
  - Blockchain.com charts API

- Output:
  - New raw CSV files under:
    - `data/raw/blockchain/`
  - All metrics aligned to UTC daily frequency.

- Planned modified files (<=2):
  - `src/ingest/onchain.py`
  - `configs/data.yaml` (only if slug list update is required)

- Acceptance commands:
  - `python -m src.cli download-data --config configs/experiment_price_onchain.yaml`
  - `pytest tests/test_no_leakage.py -v`

- Additional reporting requirement:
  After execution, report:
  - New metrics added
  - Files created
  - Row counts
  - Missing value summary

---

## Iter-1B: Factor Build Within Locked Sources

- Goal:
  - Build derived on-chain features from Blockchain raw metrics.
  - Add growth rates, rolling transforms, and ratio-based factors.
  - Maintain strict anti-leakage discipline.

- Input:
  - `data/raw/yfinance/*`
  - `data/raw/blockchain/*`
  - macro dummy switch in config

- Output:
  - Feature parquet usable by train/report stage
  - Reproducible run config for Iter-1 evaluation

- Planned modified files (<=3):
  - `src/features/onchain_factors.py`
  - `src/datasets/build_dataset.py`
  - `configs/experiment_price_onchain.yaml`

- Acceptance commands:
  - `python -m src.cli build-features --config configs/experiment_price_onchain.yaml`
  - `python -m src.cli validate --config configs/experiment_price_onchain.yaml`
  - `pytest tests/test_no_leakage.py -v`

---

## Iter-1C: Predictive Evaluation (Statistical Increment Test)

- Goal:
  - Run walk-forward comparison under identical split.
  - Compare price-only vs price+onchain.
  - Export IC-focused outputs.

- Input:
  - Iter-1B features
  - Fixed walk-forward settings

- Output:
  - `reports/ic_table.csv`
  - Intermediate metrics/preds used for report drawing

- Planned modified files (<=3):
  - `src/evaluation/walk_forward.py`
  - `src/evaluation/metrics.py`
  - `src/cli.py`

- Acceptance commands:
  - `python -m src.cli train --config configs/experiment_price_only.yaml --model lgbm`
  - `python -m src.cli train --config configs/experiment_price_onchain.yaml --model lgbm`
  - `pytest tests/test_no_leakage.py -v`

---

## Iter-1D: Report Packaging + Comparison Figures

- Goal:
  - Finalize V1 research package.
  - Generate comparison artifacts required for thesis-level documentation.

- Input:
  - Iter-1C model outputs
  - Evaluation tables

- Output:
  - `reports/ic_table.csv`
  - `reports/figures/ic_summary.pdf`
  - `reports/figures/compare_price_vs_onchain.pdf`

- Planned modified files (<=3):
  - `src/visualization/matplotlib_reports.py`
  - `src/cli.py`
  - `reports/summary.md` (format/template refresh only)

- Acceptance commands:
  - `python -m src.cli report --config configs/experiment_price_onchain.yaml --model lgbm`
  - `python -m src.cli report --config configs/experiment_price_only.yaml --model lgbm`
  - `pytest tests/test_no_leakage.py -v`

---

## V1 Success Standard

- Required minimum outputs:
  - `reports/ic_table.csv`
  - `reports/figures/ic_summary.pdf`
  - `reports/figures/compare_price_vs_onchain.pdf`
- All Iter-1A/1B/1C/1D acceptance commands pass.
- No source beyond `yfinance + Blockchain.com + macro dummy` is introduced before Iter-1D completion.
- No leakage assertion triggered during full pipeline run.

