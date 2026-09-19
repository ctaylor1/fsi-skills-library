# Domain Rules — insurance-rating-worksheet-builder

The rate manual governs (versioned). Orientation: an auditable premium buildup that applies the
documented base rate and factors, with the minimum premium made explicit. Indication only — never
a bound quote.

## Computation (deterministic)
Per coverage:
| Step | Definition |
| ---- | ---------- |
| base | `base_rate` from the manual |
| factor step | multiply the running value by each `factor.value` in the manual's order |
| `premium_before_fees` | `base_rate × Π(factor values)` |
| min-premium | if `premium_before_fees < min_premium`, raise to `min_premium` (shown as a step) |
| fees | add coverage fees |
| `coverage_total` | `max(premium_before_fees, min_premium) + Σ coverage_fees` |

Total:
| Metric | Definition |
| ------ | ---------- |
| `indicated_premium` | `Σ coverage_total + Σ policy_fees` |

Factors/rates come only from the manual; an out-of-manual factor is an exception to escalate, never
invented.

## Reporting (indication only)
- Show every step (base, each factor with its value, running total, min-premium application, fees).
- Present the result as an **indicated** premium, not a quoted or bound number.

## Hard boundaries (fail closed)
- Never bind/issue/finalize a quote or make an offer; never override the manual; never invent a
  factor; never hide the minimum premium.
