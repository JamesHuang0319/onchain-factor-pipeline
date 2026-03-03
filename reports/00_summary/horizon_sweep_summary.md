# Horizon Sweep Summary

- config_name: `iter1_price_onchain`
- model_name: `lgbm`
- horizons: `[1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90, 120, 180]`
- best horizon by IC_mean: `180`
- best horizon by RankIC_mean: `180`
- best horizon by OOS_R2_mean: `2`

## Interpretation
- IC_mean and RankIC_mean are horizon-dependent, indicating signal speed mismatch across horizons.
- OOS_R2_mean does not necessarily peak at the same horizon as IC_mean, implying trade-offs between correlation skill and squared-error fit.
- Negative IC ratio decreases at some longer horizons, consistent with potentially slower-moving on-chain signal effects.
