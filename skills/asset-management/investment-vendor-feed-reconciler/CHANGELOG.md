# Changelog - investment-vendor-feed-reconciler

## [0.1.0] - 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic internal-vs-vendor market-data reconciliation - match observations cell
  by cell across five domains (price, rating, index_constituent, corporate_action,
  instrument_attribute), classify disagreements, preserve lineage with per-source as-of times, tie
  out by completeness, and route each break. Draft-only; no canonical selection, no repair, no
  adjudication.
- **Break taxonomy (deterministic):** `value_mismatch`, `missing_in_internal`, `missing_in_vendor`,
  `stale_as_of` - each with `material`, `route`, `disposition: "UNRESOLVED"`, `canonical_value:
  null`, and internal/vendor lineage citations carrying as-of times (see
  `scripts/calculate_or_transform.py`).
- **Tie-out invariant:** completeness partition - `matched_cells + break_cells == total_cells`,
  `residual_cells == 0`; no cell dropped or double-counted.
- **Controls:** R2; HARD BOUNDARY against choosing the canonical value, overriding/repairing a
  record, adjudicating which source is correct, forcing a tie, and per-run threshold tuning;
  versioned-config tolerances/materiality/staleness/routing; `external-delivery` approval;
  segregation of duties between detection and adjudication.
- **Routing:** price discrepancies (incl. stale prices) to `valuation-exception-packet`; rating /
  instrument-attribute to `security-master-enricher`; corporate-action terms to
  `corporate-action-interpreter`; index constituents to the benchmark data owner (human review).
- **Idempotency:** `reconciliation_id` = `ivfr-{entity}-{as_of}-{input_fingerprint[:8]}` (SHA-256
  of normalized inputs) with no timestamp/random component; identical inputs reproduce identical
  output.
- **Scripts:** `validate_input` (job schema, one-observation-per-cell, matching-feasibility
  warnings), the reconciliation engine, `validate_output` (completeness tie-out, break taxonomy,
  lineage + as-of, idempotency, no-adjudication / never-repaired screen + prohibited-decision
  language screen, disclaimer). All stdlib-only with `--selftest`.
- **Evaluations:** trigger/routing (price, security-master, corporate-action, upstream detector),
  golden reconciliation with completeness tie-out, all-agree edge, deterministic script checks,
  no-adjudication safety on a non-compliant fixture (canonical value chosen, price break
  mis-routed, tie-out broken, disclaimer dropped) + injection, and external-delivery
  authorization.
- **Handoffs:** upstream `investment-data-quality-exception-detector`; downstream
  `valuation-exception-packet`, `security-master-enricher`, `corporate-action-interpreter`, and the
  benchmark data owner; boundaries `position-cash-reconciliation-assistant` and
  `nav-preparation-tie-out`. Choosing the canonical value and writing any record are
  human/authorized-system actions.

### Pending before release
- Domain SME (market-data operations / data governance) + control-owner blind review; SoD
  confirmation for detection vs adjudication.
- Confirm the versioned tolerance/materiality/staleness/routing config source and its owner, and
  each vendor feed's license/redistribution terms.
- Wire read-only MCP integrations (internal book-of-record, vendor feed, config) at deployment.
