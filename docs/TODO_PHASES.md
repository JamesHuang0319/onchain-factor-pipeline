# TODO PHASES (Executable Plan)

## Global Constraint
- Before Iter-1D completion, V1 must only use: `yfinance + Blockchain.com + macro dummy`.
- Explicitly prohibited in V1:
  - `FRED`
  - `Glassnode`
  - `CoinMetrics`
  - `Deribit`
- Each step may modify at most 3 files.
- After each step:
  - Run smoke command
  - Run pytest
  - Verify no leakage assertion triggered

---

## Step Plan

| Step | Objective | Actions | File Scope (<=3) | Acceptance Commands |
|------|-----------|---------|------------------|---------------------|
| Step-1 (Iter-1A) | Extend Blockchain ingestion | Add 4–7 new Blockchain charts slugs (fees, hashrate, difficulty, miner revenue, mempool, etc). Keep cache + retry unchanged. | `src/ingest/onchain.py` ; `configs/data.yaml` (if slug list updated) | `python -m src.cli download-data --config configs/experiment_price_onchain.yaml` ; `pytest tests/test_no_leakage.py -v` |
| Step-2 (Iter-1B) | Build derived on-chain features | Add growth rates, rolling transforms, and ratio factors. Maintain strict anti-leakage. | `src/features/onchain_factors.py` ; `src/datasets/build_dataset.py` ; `configs/experiment_price_onchain.yaml` | `python -m src.cli build-features --config configs/experiment_price_onchain.yaml` ; `python -m src.cli validate --config configs/experiment_price_onchain.yaml` ; `pytest tests/test_no_leakage.py -v` |
| Step-3 (Iter-1C) | Run incremental predictive evaluation | Train price-only vs +onchain under identical walk-forward split. Export IC table. | `src/evaluation/metrics.py` ; `src/evaluation/walk_forward.py` ; `src/cli.py` | `python -m src.cli train --config configs/experiment_price_only.yaml --model lgbm` ; `python -m src.cli train --config configs/experiment_price_onchain.yaml --model lgbm` ; `pytest tests/test_no_leakage.py -v` |
| Step-4 (Iter-1D) | Generate final research comparison artifacts | Export IC summary + comparison PDF. | `src/visualization/matplotlib_reports.py` ; `src/cli.py` ; `reports/summary.md` | `python -m src.cli report --config configs/experiment_price_only.yaml --model lgbm` ; `python -m src.cli report --config configs/experiment_price_onchain.yaml --model lgbm` ; `pytest tests/test_no_leakage.py -v` |

---

## Additional Requirement for Step-1

After Step-1 execution, you must report:

- New metrics added
- Files created
- Row counts per metric
- Missing value summary

Stop after reporting. Do not continue to Step-2 automatically.

---

## V1 Done Definition

- `reports/ic_table.csv` exists.
- `reports/figures/ic_summary.pdf` exists.
- `reports/figures/compare_price_vs_onchain.pdf` exists.
- All step acceptance commands pass.
- No source beyond `yfinance + Blockchain.com + macro dummy` is introduced before Iter-1D completion.
- No leakage assertion triggered during full pipeline.