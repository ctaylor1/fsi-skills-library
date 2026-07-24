# Domain Rules — capital-structure-maturity-mapper

Orientation: a factual, source-linked view of the debt stack and maturity profile. Description
only — never advice.

## Computation (deterministic)
| Metric | Definition |
| ------ | ---------- |
| `total_debt` | Σ principal (single currency) |
| `by_seniority` / `by_type` | Σ principal grouped by seniority / instrument type |
| `secured_unsecured` | Σ principal split by the `secured` flag |
| `maturity_wall` | Σ principal grouped by `maturity_date` year; undated → `undated` bucket |
| `wam_years` | `Σ(principal × years_to_maturity) / Σ principal`, years = (maturity − as_of)/365.25 |
| `wac_pct` | `Σ(principal × coupon_pct) / Σ principal` |
| `near_term_24m` | Σ principal maturing within 24 months of as_of |

Instruments missing principal or maturity are excluded from the affected metric and flagged.
Mixed currencies are **not** summed; they are grouped and flagged.

## Reporting (description only)
- Present buckets and weighted averages as facts, each tied to source lines.
- Never rank, label, or recommend; never call any structure optimal.

## Hard boundaries (fail closed)
- Never give financing advice or a recommendation; never sum mixed currencies without a supplied
  FX basis; never impute missing principal/maturity.
