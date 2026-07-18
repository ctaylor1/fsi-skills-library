# Domain Rules — portfolio-risk-diversification-check

Explainable diversification/concentration **checks** and how they map to a descriptive
**diversification band**. Thresholds are configuration (versioned, owned by the
risk/portfolio-analytics team), not hard-coded judgments, and never tuned to an individual
investor's holdings to reach a desired conclusion. Every figure is a transparent function of
the position weights and the bundled reference data (sector/region/asset-class taxonomy,
factor loadings, correlation matrix). Orientation references: the firm's risk-analytics
standard and published diversification/concentration measurement conventions take precedence.

## Check taxonomy

| Check | Flags when (default config) | Evidence attached |
| ----- | --------------------------- | ----------------- |
| `single_name_concentration` | Any position weight > `single_name_max` (default 10%) | The position(s) + weight |
| `topN_concentration` | Sum of top-`topn` (default 5) weights > `topn_max` (default 40%) | Top-N positions + cumulative weight |
| `sector_concentration` | Largest sector weight > `sector_max` (default 30%) | Sector + weight + constituents; sector HHI |
| `geography_concentration` | Largest region weight > `geography_max` (default 50%) | Region + weight |
| `asset_class_concentration` | Largest asset-class weight > `asset_class_max` (default 90%) | Asset class + weight |
| `factor_tilt` | Any weighted factor tilt \|Σ wᵢ·loadingᵢ\| > `factor_band` (default 0.50) | Factor(s) + tilt |
| `correlation_concentration` | Average pairwise correlation > `corr_max` (default 0.60) | Avg correlation + highest pairs + n_pairs |
| `liquidity_concentration` | Weight in the illiquid bucket (days-to-liquidate > `liquidity_days_threshold`, default 7) > `illiquid_weight_max` (default 15%) | Illiquid holdings + weight |

Checks are **additive and independent**; the output reports each that flagged with its own
evidence, plus always-reported summary metrics (HHI, effective number of holdings = 1/HHI,
top-N weight). There is no opaque composite "risk score" and no forecast of returns.

A check that lacks its required inputs (no sector data, no factor loadings, no correlation
matrix, no liquidity days) is reported under `not_evaluable`, never silently treated as
passing.

## Diversification band mapping (deterministic, documented)

| Band | Rule |
| ---- | ---- |
| **Well-diversified** | 0 checks flagged |
| **Moderately concentrated** | 1–2 checks flagged, none of them an escalator |
| **Highly concentrated** | ≥ 3 checks flagged, OR any escalator flagged (`single_name_concentration`, `correlation_concentration`) |

`single_name_concentration` and `correlation_concentration` are escalators because a single
oversized position, or holdings that move together, undermine diversification even when the
nominal count of holdings is large.

The band is a **descriptive summary of exposures**, not a suitability rating, a
recommendation, or a prediction. It is derived deterministically so
`scripts/validate_output.py` can re-derive it and tie it out.

## Hard boundaries (fail closed)

- Never provide **personalized investment advice** or a **recommendation** to buy, sell,
  hold, allocate, rebalance, trim, or add to any security or asset class.
- Never make a **suitability** or "right for you" judgment, or state that a holding is a
  "good/bad investment".
- Never **forecast** returns, prices, or performance ("will outperform", "expected to rise",
  "guaranteed returns", price targets).
- Never tune thresholds to the individual portfolio to manufacture a conclusion; use only the
  versioned config.
- Concentration, correlation, and factor figures describe **current exposures under the
  bundled reference data** — state their model-dependence, do not present them as certainties.

## Educational prompts (always include when any check flagged)

Concentration can reflect a deliberate, informed strategy; diversification metrics depend on
the classification scheme and window; correlations change over time and rise in stressed
markets; factor and correlation figures are model estimates; and whether the exposures fit an
investor's objectives, horizon, liquidity needs, and risk tolerance is a question for the
investor and a **licensed financial professional**. The profile must surface these so the
reader weighs context rather than reading the band as a verdict.
