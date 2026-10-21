# Changelog

## 2026-09-20 — Phase 1 explicit-mode merge (unreleased)

- Consolidated the two named entrypoints without merging their native schemas or professional responsibilities.
- Added whitelist dispatch, validation before compute, detached native/outer reconstruction and mode-isolation regressions.
- Preserved native fixtures and evaluation declarations under mode-prefixed script and case identifiers.
- No automatic cross-mode mapping, source connector or execution authority added.
- Updated routing identifiers to canonical package names; self-handoffs require explicit modes and reviewed native-input preparation. Added detached wrapper fixtures and standalone/mode-isolation regressions.

## data_quality mode: investment-data-quality-exception-detector

# Changelog — investment-data-quality-exception-detector

## 2026-09-20 — Phase 1 development corrections (unreleased)

- Repaired bounded native methods and disclosed their supported scope; see domain-rules and schema.
- Added detached original-input reconstruction, finite-JSON hashing and rejection of unvalidated output fields.
- Revised synthetic fixtures and independent operation regressions; no production, professional or institutional acceptance claimed.


## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort, Wave 5).

- **Scope:** deterministic data-quality detection over approved investment feeds — six checks
  (`stale_price`, `implausible_move`, `absent_factor`, `duplicate_instrument`,
  `conflicting_classification`, `broken_mapping`) producing an evidence-cited, prioritized
  exception queue with a durable `exception_queue_id`. Read-only; no correction, no
  suppression, no canonical-value choice.
- **Controls:** R2; hard boundary against silently correcting/overriding/filling a value,
  suppressing/waiving/closing an exception, and choosing the canonical feed; versioned-config
  thresholds and severities only; standing disclaimer required; `external-delivery` approval.
- **Scripts:** `validate_input` (snapshot schema, evaluability warnings), the check engine
  `calculate_or_transform` (evidence + severity + deterministic `queue_priority` P1–P4 +
  routing), and `validate_output` (the prohibited-decision screen: evidence/as-of
  completeness, severity/priority tie-out, `status: open` enforcement, forbidden
  correction/override field scan, reference-data-conflict routing, correction/suppression/
  advice language screen, disclaimer).
- **Routing:** reference-data conflicts → `investment-vendor-feed-reconciler`; identity/mapping
  conflicts → `security-master-enricher` / the security-master steward; upstream normalization
  from `holdings-transaction-normalizer`.
- **Evaluations:** trigger/routing, golden P1 queue over a bundled snapshot, no-prev-price
  edge, deterministic script checks, a non-compliant safety fixture that must fail closed, an
  injection safety case, and external-delivery authorization.

### Pending before release
- Domain SME (investment-data governance) + control-owner blind review.
- Confirm the versioned DQ threshold/severity config source and its owner; confirm the
  per-asset-class `move_band` and required-factor sets.
- Confirm the `nav_impacting` / material-weight definition used for severity escalation.
- Wire read-only MCP integrations (market-data/pricing, security-master/reference-data,
  entity resolution, config) at deployment.


## vendor_feed mode: investment-vendor-feed-reconciler

# Changelog - investment-vendor-feed-reconciler

## 2026-09-20 — Phase 1 development corrections (unreleased)

- Repaired bounded native methods and disclosed their supported scope; see domain-rules and schema.
- Added detached original-input reconstruction, finite-JSON hashing and rejection of unvalidated output fields.
- Revised synthetic fixtures and independent operation regressions; no production, professional or institutional acceptance claimed.


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
