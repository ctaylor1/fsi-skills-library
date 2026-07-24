# Changelog — investment-data-quality-exception-detector

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
