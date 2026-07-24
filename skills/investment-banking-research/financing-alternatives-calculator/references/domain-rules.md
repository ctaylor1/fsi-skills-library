# Domain Rules — financing-alternatives-calculator

Orientation: a factual, reproducible cost/impact comparison across documented financing
alternatives. Numbers only — never a recommendation.

## Computation (deterministic)
For **debt** alternatives (term_loan, bond, etc.):
| Metric | Definition |
| ------ | ---------- |
| `annual_interest` | `amount × rate_pct / 100` |
| `upfront_fees` | `amount × fees_pct / 100` |
| `amortized_fees_annual` | `upfront_fees / term_years` |
| `all_in_annual_cost` | `annual_interest + amortized_fees_annual` |
| `effective_cost_pct` | `all_in_annual_cost / amount × 100` |
| `total_cost_over_term` | `annual_interest × term_years + upfront_fees` |

For **equity** alternatives:
| Metric | Definition |
| ------ | ---------- |
| `shares_issued` | `amount / share_price` |
| `dilution_pct` | `shares_issued / (current_shares + shares_issued) × 100` |
| interest metrics | 0 / not-applicable (equity has no coupon) |

A missing term makes the affected metric `null` (not-computable); market rates are never assumed.

## Reporting (numbers only)
- One row per alternative with every metric and the terms used.
- No ranking, no "cheapest/best/optimal", no highlighted winner.

## Hard boundaries (fail closed)
- Never recommend, rank, or advise which alternative to choose; never assume a missing rate;
  never combine mixed currencies; never net equity dilution against debt interest.
