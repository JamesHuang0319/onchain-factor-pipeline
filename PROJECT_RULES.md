# PROJECT RULES (must follow)

## Research Objective
This project studies whether blockchain-native on-chain factors provide incremental predictive power for future crypto returns.

Primary research focus:
- Incremental statistical value (IC, RankIC, OOS R²)
- Stability across time
- Robustness to walk-forward validation

Secondary focus:
- Economic significance via backtesting

---

## Non-Negotiables

### Anti-Leakage
- NO FUTURE LEAKAGE.
- Features at t must use information <= t only.
- Label defined as log_ret_7d = log(close_{t+7}/close_t).
- Rolling statistics must not peek forward.
- On-chain forward-fill allowed; backward-fill strictly forbidden.
- Macro factors must respect release_lag_days.

### Validation Discipline
- Walk-forward only (chronological split).
- No shuffling.
- Any model comparison must use identical splits.

### Data Discipline
- All downloads cached under data/raw.
- If cache exists and force=false, DO NOT call network.
- All timestamps converted to UTC date.
- No duplicate (date, asset) keys allowed.

---

## Development Discipline

- Modify at most 1-3 files per step.
- After each step:
  - run smoke command
  - run pytest
  - report metric deltas

### Environment & Run Commands

> **IMPORTANT**: The project uses a dedicated conda environment named `crypto_predict`.
> The default `python` on PATH (e.g., `E:\Python311\python.exe`) is missing project dependencies.

Always run commands within the `crypto_predict` conda environment.

```powershell
# Activate the environment
conda activate crypto_predict

# Correct: run tests
pytest tests/test_no_leakage.py -v -p no:cacheprovider

# Correct: run pipeline
python -m src.cli <command> --config <config>
```

Never use bare `python` or `pytest` in pwsh without activating the `crypto_predict` conda environment first.

### Git Workflow (Mandatory)

- Never develop directly on `main`.
- Each functional step must use a dedicated branch:
  - Naming convention: `iter-<IterName>-<StepName>`
- Each step must be logically isolated and reproducible.
- Each completed step must generate a report under:
  - `docs/step_reports/`
- Before committing:
  - output a completion checklist
  - wait for manual confirmation
- Only after explicit confirmation:
  - git add
  - git commit
  - git push
- Merge to `main` only after explicit approval.

---

## Repo Conventions

- Python 3.11 (match actual environment)
- pathlib for all paths
- Matplotlib for research figures (PDF only)
- Plotly only for trading visual diagnostics
- All new modules must include docstring and type hints