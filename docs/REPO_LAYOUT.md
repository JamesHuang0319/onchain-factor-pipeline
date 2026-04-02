# Repo Layout Rules

## Keep at Project Root
- `PROJECT_RULES.md`
  - Project governance and non-negotiable engineering/research rules.
- `requirements.txt`
  - Environment dependency lock for reproducibility.
- `论文.pdf`
  - Primary reference paper file for method alignment.

These three files should stay in root for visibility and quick access.

## Put in `docs/`
- Methodology and research writing content only:
  - `PROJECT_PLAN.md`
  - `METHODOLOGY.md`
  - `EXPERIMENTS.md`
  - `THESIS_NOTES.md`
  - `REPO_LAYOUT.md`

Do not place generated CSV/PDF/HTML experiment artifacts in `docs/`.

## Put in `reports/`
- All generated experiment outputs:
  - CSV tables
  - plots
  - trading charts
  - summary files

`reports/` is disposable/rebuildable; `docs/` is narrative/reference.
