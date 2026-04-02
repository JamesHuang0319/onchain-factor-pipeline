# Implementation Roadmap

## Phase 1: Stabilize BTC daily baseline
1. Keep the scope fixed to `BTC-USD`, daily frequency, single-asset.
2. Run the full ML matrix on:
   - `onchain`
   - `ta`
   - `all`
   - `boruta_onchain`
   - `boruta_ta`
   - `boruta_all`
   - `univariate`
3. Compare both tasks:
   - `classification` for direction
   - `regression` for magnitude
4. Select the strongest ML baseline by:
   - out-of-sample metrics
   - walk-forward stability
   - backtest profitability

## Phase 2: Improve on-chain coverage without Glassnode
1. Keep current `Blockchain.com` metrics as the low-cost baseline.
2. Add `Coin Metrics Community API` as the first expansion source.
3. Expand factors in coherent blocks:
   - activity
   - transfer value
   - miner/network security
   - valuation/profitability if available
4. Prefer factor families with clear interpretation over metric-count inflation.

## Phase 3: Make the project usable for live-style daily inference
1. Rebuild the latest feature row without dropping unlabeled tail rows.
2. Fit the selected model on full history available before prediction date.
3. Output:
   - direction prediction
   - magnitude prediction
   - feature date / prediction date
4. Save latest prediction artifacts under `reports/00_summary/latest_predictions/`.

## Phase 4: Optional model expansion
1. Finish ML comparison first.
2. Add only 1-2 DL baselines after the ML baseline is stable:
   - `LSTM`
   - `TCN` or `CNN-LSTM`
3. Treat DL as a comparison block, not the project core.

## Immediate Engineering Priorities
1. Verify `Coin Metrics` metrics that are available in the community tier.
2. Run `download-data`, `build-features`, and `predict-latest` with both `blockchain` and `coinmetrics`.
3. Refine backtest mapping so classification and regression signals use explicit trading rules.
4. Decide the final pair:
   - best direction model
   - best magnitude model
