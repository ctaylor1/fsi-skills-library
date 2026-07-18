# Domain Rules — valuation-reviewer

Explainable valuation-review **checks** and how the fired set maps to a **review-disposition
band**. Thresholds are configuration (versioned, owned by the valuation-control / product-
control function), not hard-coded judgments, and never tuned to a desk to make a mark pass.
The firm's valuation policy, the fair-value-measurement hierarchy standard, and independent-
price-verification (IPV) standard take precedence over anything here.

## Check taxonomy

| Check | Severity | Fires when (default config) | Evidence attached |
| ----- | -------- | --------------------------- | ----------------- |
| `hierarchy_consistency` | high | A significant **unobservable** input is present but the declared fair-value level is lower than the level that implies (under-classification) | Declared level + implied minimum |
| `input_staleness` | medium | Any input `source_date` older than `max_staleness_days` (default 10) before `as_of` | Stale input rows + ages |
| `input_source_missing` | medium | Any input has no `source_ref` (untraceable evidence) | The untraceable input rows |
| `ipv_missing` | high | Level 2/3 valuation with no performed independent price verification | IPV-required marker |
| `ipv_breach` | high | `|reported − independent| / reported` exceeds `ipv_tolerance_pct` (default 1.0%) **and** no documented rationale | Independent vs reported + variance |
| `unexplained_adjustment` | medium | Any adjustment lacks rationale/source, **or** its magnitude ≥ `adjustment_materiality_pct` (default 5%) of reported value with no approver | The adjustment rows |
| `comparable_sufficiency` | medium | **Market** approach with fewer than `min_comparables` (default 3) comparables | Comparable count |
| `uncertainty_missing` | medium | **Level 3** valuation with no documented valuation-uncertainty / sensitivity range | Level-3 record marker |
| `override_unapproved` | high | Any manual override lacks a recorded approver or rationale | The override rows |

Checks are **independent and evaluable-on-data**: a check whose data is absent (e.g.
`comparable_sufficiency` for an income-approach mark, `ipv_missing` for Level 1) is reported
under `not_evaluable`, never silently passed. There is no opaque composite "valuation score".

## Disposition mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Pass with observations** | 0 findings fired |
| **Findings raised** | ≥ 1 finding fired, all medium severity, and fewer than `escalate_finding_count` (default 4) |
| **Escalate** | Any **high**-severity finding fired, OR ≥ `escalate_finding_count` findings fired |

The disposition is a **triage suggestion for a human reviewer / the Valuation Control
Committee**. It is not a valuation sign-off, an override approval, or a fair-value
determination, and it never posts a value.

## Hard boundaries (fail closed)

- Never **sign off** a valuation, **approve** an override or adjustment, or state a mark is
  "correct / accurate / fair value" — describe the evidence and attribute any conclusion to
  the authorized approver.
- Never **post, book, or write** a value to the GL / subledger / system of record.
- Never provide **personalized investment advice** or a price target dressed as a review.
- Never **tune thresholds** to make a specific mark pass; use only the versioned config.
- Never restate a desk/trader mark as independently verified when IPV is missing, stale, or
  breached.

## Review considerations (always include when any finding fired)

A documented and approved policy/methodology exception, a genuinely thin or inactive market
where comparables are scarce, an immaterial adjustment magnitude, an input refreshed after
the extract, an IPV variance within an approved asset-class tolerance band, or an override
pre-approved under a standing delegated authority. The pack must invite the reviewer to weigh
these benign explanations before concluding.
