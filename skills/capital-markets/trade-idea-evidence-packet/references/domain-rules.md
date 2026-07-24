# Domain Rules — trade-idea-evidence-packet

Orientation: a cited, risk-balanced evidence packet backing a trade thesis for internal review.
Evidence only — never a client recommendation or a suitability determination.

## Sections assembled (deterministic)
- `thesis` — the idea statement (instrument, direction, rationale).
- `evidence` — supporting data points, each with a citation.
- `risk_factors` — the risks to the thesis.
- `suitability_flags` — surfaced flags (see below), not a determination.

## Checks (deterministic)
| Check | Rule | Gap/flag when |
| ----- | ---- | ------------- |
| `citation_coverage` | Every data point has a non-empty `source_ref` | A data point is uncited |
| `risk_balance` | At least one risk factor is present | No risk factors provided |
| `restricted_product` | Instrument not on `restricted_products` | Instrument is restricted → flag, route to compliance |
| `general_only` | If `general_only` is set, note that the packet is general, not tailored | Always noted when set |
| `section_completeness` | Every `required_section` is present | A required section is missing |

Configs are **versioned contracts**; restricted lists/rules are never guessed.

## Disposition mapping (review-only)
- `packet-ready` — all data points cited, ≥1 risk factor, all sections present, no restricted flag.
- `gaps-for-review` — an uncited claim, missing risk factors, a restricted flag, or a missing
  section. A triage suggestion for the human/compliance, **not** a recommendation.

## Hard boundaries (fail closed)
- Never recommend to a specific client; never determine suitability/eligibility; never give
  investment advice; never present uncited claims as evidence; never clear a restricted product.
