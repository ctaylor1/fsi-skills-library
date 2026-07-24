# Domain Rules — claim-damage-evaluation-comparator

Orientation: fair, documented claim evaluation. This skill surfaces line-item anomalies for the
adjuster; it never values the claim.

## Normalization
- Description normalized: lowercased, punctuation stripped, whitespace collapsed.
- Grouping key: `(category, normalized_description)`. Items group **only** on an exact key match;
  near-matches are reported as data gaps, never merged.
- Amounts rounded to cents for comparison.

## Checks (deterministic)
| Check | Definition | Finding when |
| ----- | ---------- | ------------ |
| `duplicate` | Same group, same amount, appearing on ≥2 distinct documents | Potential double-count across documents |
| `difference` | Same group with ≥2 distinct amounts | Same item priced differently across documents |
| `unsupported` | A line item whose `supported_by` is empty (and its category requires support) | Item has no linked supporting document |

Config (`categories_requiring_support`, rounding) is a documented contract; the output records
what it used. Findings are factual observations, never valuations.

## Disposition mapping (review-only)
- `clean` — no findings.
- `items-for-review` — ≥1 finding. A triage suggestion for a human reviewer, **not** a valuation
  or a settlement determination.

## Hard boundaries (fail closed)
- Never set/value/recommend damages, reserve, or settlement; never determine coverage/liability;
  never approve payment; never net or sum into a recommended figure.
