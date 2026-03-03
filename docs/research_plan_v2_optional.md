# Research Plan V2 Optional (Not in V1)

## Positioning
- This document lists optional future extensions only.
- These sources are explicitly **excluded from V1** and can be considered only after Iter-1D is finished.

## Optional Data Sources (Future)
## FRED (Macro Real Data)
- Purpose: replace macro dummy with real-time vintage-aware macro signals.
- Example use: rates, inflation, liquidity proxies with release-lag handling.
- Entry condition: V1 deliverables completed and leakage controls extended for macro vintage alignment.

## Glassnode
- Purpose: richer on-chain coverage (exchange flows, holder structure, valuation metrics).
- Example use: netflow/inflow/outflow, NVT variants, supply cohorts.
- Entry condition: V1 comparison package stable; source-governance tests added.

## CoinMetrics
- Purpose: standardized network + market datasets with broad asset coverage.
- Example use: multi-asset panel expansion and factor consistency checks.
- Entry condition: V1 single-pipeline reproducibility complete.

## Deribit
- Purpose: derivatives and sentiment/risk-premium proxies.
- Example use: funding, open interest, implied volatility/skew.
- Entry condition: V1 statistical/economic baseline finalized and report template versioned.

## Suggested V2 Activation Order
1. FRED
2. Glassnode or CoinMetrics (choose one first, not both at once)
3. Deribit

## V2 Guardrails
- Keep one-source-at-a-time onboarding to preserve attribution of metric changes.
- Maintain anti-leakage assertions for each newly added source.
- Preserve V1 as immutable benchmark branch/tag for thesis comparability.
