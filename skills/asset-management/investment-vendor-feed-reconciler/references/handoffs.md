# Adjacent-Skill Handoffs - investment-vendor-feed-reconciler

This skill produces a field-level discrepancy pack - a classified break list with per-source
values, as-of times, lineage, and per-break routing (durable `reconciliation_id`), then stops.
It does not choose the canonical value, repair or override any record, resolve a valuation,
interpret corporate-action terms, or reconcile positions/cash/NAV.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `valuation-exception-packet` | Any **price** discrepancy (mismatch or stale price) - the price is worked as a valuation exception, never adjudicated here (mandatory route) | `reconciliation_id` + the price break rows with both sources' values/as-of |
| `security-master-enricher` | **Rating / instrument-attribute** disagreements or missing fields that need a reference-data enrichment proposal under steward approval | `reconciliation_id` + the reference-data break rows |
| `corporate-action-interpreter` | **Corporate-action term** disagreements (ex/record/pay dates, ratio, option terms) needing interpretation against the authoritative notice | `reconciliation_id` + the corporate-action break rows |
| index / benchmark data owner (human review) | **Index-constituent** membership or weight disagreements - no catalog skill owns this; hand to the benchmark data owner | `reconciliation_id` + the constituent break rows |

## Upstream (may call this skill)

`investment-data-quality-exception-detector` screens a **single** feed for stale prices, absent
factors, duplicate instruments, implausible moves, and broken mappings, and **routes genuine
cross-source reference-data conflicts to this skill**. This skill consumes the flagged
instruments/fields and performs the internal-vs-vendor field-level comparison; it does not
re-run single-source anomaly detection.

## Choosing the canonical value (human / authorized system)

There is **no catalog skill that selects a canonical value or writes the security master**, by
design. The canonical-value decision (and any resulting record write) is made by an **authorized
human under data-governance controls** - typically after the routed downstream skill assembles the
evidence. This skill hands over the disagreement and its lineage; the decision and the write
happen outside it.

## Not this skill (route elsewhere)

- **Positions / cash vs custodian, prime broker, or administrator** -> `position-cash-reconciliation-assistant`,
  not vendor reference/market-data reconciliation.
- **NAV tie-out** across books, custodian, and administrator (prices, accruals, income, shares,
  cash) -> `nav-preparation-tie-out`; price issues it finds route to `valuation-exception-packet`,
  the same downstream this skill uses.

## Duplicate-execution prevention

- This skill **classifies and routes cross-source discrepancies only**; it must not choose the
  canonical value, override/repair a record, resolve a valuation, or interpret corporate-action
  terms - those belong to the human reviewer and the downstream skills above.
- Downstream owners reuse the `reconciliation_id`, breaks, and lineage rather than recomputing the
  comparison.
