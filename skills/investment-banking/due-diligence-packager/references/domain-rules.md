# Domain Rules — due-diligence-packager

Orientation: buy-side/sell-side commercial due-diligence practice. The engagement's diligence
scope and the deal team's checklist are the authoritative, versioned contract; the taxonomies
below are configurable defaults used by the deterministic packaging engine.

## Required diligence workstreams (completeness)

The completeness check compares covered workstreams (evidenced by sources, extractions, or
issues) against this required set. Missing workstreams are **listed explicitly**, never
implied as covered.

| Workstream | Typical evidence |
| ---------- | ---------------- |
| `financial` | Audited/mgmt financials, quality-of-earnings inputs, net debt, working capital |
| `legal` | Corporate records, material contracts, change-of-control, litigation |
| `tax` | Returns, provisions, uncertain positions, transfer pricing |
| `commercial` | Customer concentration, pipeline, contracts, market position |
| `operational` | Supply chain, IT/systems, facilities, KPIs |
| `hr` | Census, compensation, benefits, key-person and retention |

A pack covering fewer than all six is valid but must report the gap. Add jurisdiction- or
sector-specific workstreams (e.g., `regulatory`, `environmental`) via the engagement config.

## Issue severity and open-question priority

| Level | Issue meaning | Open-question priority |
| ----- | ------------- | ---------------------- |
| `high` | Potential deal-breaker or price-impacting; needs resolution before signing | Blocking; owner + due date required |
| `medium` | Material but manageable; feeds diligence findings and reps/warranties | Should-have before final review |
| `low` | Informational or immaterial | Nice-to-have |

Severity/priority are **triage labels for the deal team**, not conclusions. This skill never
downgrades or resolves an issue on the target's behalf.

## Citation & unsupported-claim rule (fail closed)

- Every extracted data point and every issue must carry a `source_doc` that resolves to a
  document in the `source_index`, plus a page/version citation.
- An item whose `source_doc` is **not** in the index is an **unsupported claim**: it is
  excluded from the pack and listed under `needs-source`. It is never "cited to the data
  room" or inferred.
- Public/filing/market figures may corroborate but never replace a data-room citation.

## Extraction confidence

`high` (directly stated in a primary source), `medium` (derived/aggregated from primary
sources), `low` (indicative; flag for confirmation). Confidence is recorded on every
extraction; `low`-confidence figures are flagged for the reviewer.

## Known model-handoff targets (must be real catalog skills)

Model bundles may target only: `three-statement-model-builder`, `dcf-modeler`,
`lbo-model-builder`, `merger-model-builder`, `comps-analysis-builder`,
`scenario-sensitivity-generator`. Any other target is an **invalid handoff** and is flagged,
not emitted. The financial-extraction bundle (revenue, EBITDA, net debt, and related fields)
is the standard payload; operating metrics accompany a `comps-analysis-builder` handoff.

## Hard boundaries (fail closed)

- No **send/submit/delivery** of the pack; no **filing** or system-of-record write.
- No **valuation opinion or investment recommendation** (buy/sell/hold, price target,
  "should acquire", guaranteed return); no personalized investment/legal/tax advice.
- No **unsupported claims**; no figure without a resolvable data-room citation.
- No **invented downstream skill**; model handoffs target known skills only.
- No **implied completeness**; missing workstreams are always reported.

## Approvals (recorded before external delivery)

The approvals ledger must record a `diligence_lead` and a `quality_reviewer`. `external_delivery`
may be `true` only when both are `approved` (with approver and date). Until then the pack is an
internal draft; delivery is a separate human action.
