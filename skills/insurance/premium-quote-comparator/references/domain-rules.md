# Domain Rules — premium-quote-comparator

Deterministic **normalization** and **difference** rules that put quotes on a like-for-like
basis. Multipliers and crosswalks are configuration (versioned, owned by the pricing/actuarial
team), not hard-coded judgments. Nothing here selects a policy or advises the customer.

## Premium + fee normalization

Quotes arrive on different payment frequencies and fee structures. To compare, everything is
converted to a **12-month annualized basis**.

| Input | Rule (default config `quote-normalize-2026.07`) |
| ----- | ----------------------------------------------- |
| `premium.frequency` | Payments per year: `annual`=1, `semiannual`=2, `quarterly`=4, `monthly`=12 |
| `annualized_premium` | `premium.amount × payments_per_year` |
| `annualized_fees` | `sum(fees.amount) × (12 / term_months)` |
| `annualized_total_cost` | `annualized_premium + annualized_fees` |
| `cost_spread` | `min`, `max`, and `delta` of `annualized_total_cost` across quotes |

`lowest_annualized_total_cost_quote_id` is the deterministic argmin (tie-break by `quote_id`).
It is a **factual figure**, not a recommendation, and is never presented without the
comparability flags below.

## Comparison grid

Build the union of coverage codes (first-seen order). For each code and each quote record
whether it is `included`, and its `limit` and `deductible`, each cited to the source quote.

## Difference taxonomy

| Difference | Fires when |
| ---------- | ---------- |
| `coverage_differences` | A coverage code is not present in all quotes |
| `deductible_differences` | Deductibles differ for a coverage shared by ≥2 quotes |
| `limit_differences` | Limits differ for a coverage shared by ≥2 quotes |
| `exclusion_differences` | An exclusion is present in some quotes but not all |
| `endorsement_differences` | An endorsement/rider is present in some quotes but not all |
| `term_differences` | `term_months` differs across quotes |

## Comparability flags (always surface when relevant)

Each material difference raises a flag so a cheaper premium is never read in isolation:
`coverage_mismatch`, `deductible_mismatch`, `limit_mismatch`, `exclusion_mismatch`,
`endorsement_mismatch`, `term_mismatch`, `currency_mismatch`. Every flag names the affected
quotes. A lower annualized cost frequently reflects a higher deductible, a lower limit, a
dropped coverage, or an extra exclusion — the flags make that explicit.

## Hard boundaries (fail closed)

- Never **recommend, select, or rank-as-advice** a quote; report the lowest cost as a fact.
- Never give **insurance/suitability advice** or judge whether coverage fits the customer's
  exposures (route to `coverage-gap-analyzer`).
- Never make a **coverage or eligibility determination** ("you are covered", "you qualify").
- Never **reconcile away** a currency/term/limit/deductible/coverage mismatch silently.

## Gotchas encoded here

- **Installment loading**: `monthly × 12` can exceed a pay-in-full annual premium because of
  installment fees; annualization compares payment schedules, not the pay-in-full price.
- **ACV / unlimited limits**: non-numeric limit values (e.g. `"ACV"`) are compared as strings;
  a `null` limit means the coverage is not included, not "unlimited".
- **Service factors** (AM Best rating, NAIC complaint index) are shown for context and are
  **not** scored or weighted into any ranking.
