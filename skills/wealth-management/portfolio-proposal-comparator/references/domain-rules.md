# Domain Rules — portfolio-proposal-comparator

Deterministic **comparison metrics**, **flag thresholds**, and the **assumption chain**. Thresholds
and tax assumptions are configuration (versioned, owned by Wealth Management advisory & compliance),
never hard-coded judgments and never tuned to an individual proposal or client. The firm's suitability,
Reg BI, and conflicts standards take precedence; this skill compares and evidences, it does not decide.

## Per-proposal metrics (deterministic)

| Metric | Definition |
| ------ | ---------- |
| `expense_weighted_bps` | Σ(weight × holding expense ratio bps) |
| `total_cost_bps` | `expense_weighted_bps` + `advisory_fee_bps` |
| `tax_cost_estimate_bps` | `assumed_turnover` × `assumed_gain_fraction` × `assumed_tax_rate` × 10,000 (approved-assumption estimate; **not** tax advice) |
| `allocation` | Weight by `asset_class` (equity / fixed_income / alternatives / …) |
| `max_issuer_weight` | Largest single-issuer weight across **single-name** holdings (diversified funds excluded via look-through) |
| `max_sector_weight` | Largest single-sector weight, excluding broad/diversified/aggregate labels |
| `illiquid_pct` | Σ weight of holdings marked `illiquid` |
| `proprietary_pct` | Σ weight of holdings marked `proprietary` |

## Flag thresholds (default config)

| Flag | Dimension | Fires when (default) | Evidence attached |
| ---- | --------- | -------------------- | ----------------- |
| `concentration_issuer` | concentration | `max_issuer_weight` > `concentration_issuer_max` (0.25) | The single-name holdings for that issuer |
| `concentration_sector` | concentration | `max_sector_weight` > `concentration_sector_max` (0.40) | The holdings in that sector |
| `liquidity` | liquidity | `illiquid_pct` > `illiquid_max_pct` (0.15) | The illiquid holdings + liquidity days |
| `conflict_proprietary` | conflicts | `proprietary_pct` > 0 | The proprietary holdings |
| `conflict_revenue_sharing` | conflicts | proposal `revenue_sharing` is true | The proposal-level flag |
| `conflict_share_class` | conflicts | any holding has `cheaper_share_class_available` | The costlier-share-class holdings |
| `objective_mismatch` | objectives | `stated_objective` given and a proposal's `objective` differs | The proposal objective vs stated |
| `cost_dispersion` | costs | a proposal's `total_cost_bps` exceeds the cheapest proposal by > `cost_dispersion_bps` (20) | The cost delta vs cheapest |

Flags are **additive and independent** and are attached to the specific proposal(s) they concern. There
is no composite "best proposal" score, no ranking, and no winner column — the matrix reports values only.

## Concentration look-through

Single-issuer and single-sector limits apply to **single-name** exposure and **true sector bets**, not
to broad/diversified funds. A holding is excluded from issuer concentration when `diversified: true`, and
excluded from sector concentration when its `sector` is a broad/diversified/aggregate label. This
prevents a diversified index fund from falsely reading as concentrated. Confirm the `diversified` flag
from product data.

## Assumption transparency (always stated in output)

- Tax-drag basis: `assumed_turnover × assumed_gain_fraction × assumed_tax_rate`; an estimate, not the
  client's actual tax outcome and not tax advice.
- Costs are gross of any account-level fee waivers or negotiated discounts.
- Risk is represented by stated allocation and concentration, not a forward return/volatility forecast;
  no outcome is guaranteed.
- Broad/diversified funds are excluded from single-issuer and single-sector limits.
- The comparison is even-handed: no proposal is scored, ranked, or selected.

## Hard boundaries (fail closed)

- Never select, rank, or recommend a proposal; never state or imply one is the "best/right/suitable"
  choice. Attribute the decision to the licensed advisor.
- Never make a suitability/Reg BI determination or give personalized investment/tax advice.
- Never recommend or take a trade, rebalance, filing, or system-of-record write.
- Never tune a threshold to make a proposal pass or fail; use the versioned config and record its
  version.
- Describe conflicts (proprietary, revenue-sharing, share-class) factually; disclose, do not minimize.
