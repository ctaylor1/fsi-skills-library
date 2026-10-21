# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — investment-record-normalizer

## 2026-09-20 — Phase 1 development corrections (unreleased)

- Repaired bounded native methods and disclosed their supported scope; see domain-rules and schema.
- Added detached original-input reconstruction, finite-JSON hashing and rejection of unvalidated output fields.
- Revised synthetic fixtures and independent operation regressions; no production, professional or institutional acceptance claimed.


## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (Wave 5, 2026 industry-expansion cohort; baseline
status: `new`). R2 / Utility domain-workflow normalizer for asset-management investment-data
operations.

- **Scope:** map positions, cash, orders, and transactions from custodian, fund-administrator,
  OMS, and accounting/GL schemas into the approved canonical schema, 1:1, with full lineage;
  route unmappable records to a reason-coded rejected-record queue; emit a reconciliation count.
- **Hard boundary:** never merge identities/deduplicate, never overwrite source records, never
  choose a canonical value across conflicting sources, never reconcile/tie-out, never advise —
  each conflict is routed via a reject reason code to the correct adjacent skill and a human.
- **Scripts:** `validate_input` (bundle envelope, lineage-key uniqueness, evaluability warnings);
  `calculate_or_transform` (deterministic mapping via a versioned ruleset, lineage + immutable
  `source_hash`, deterministic `canonical_id`/`job_id`, reject routing, self-check invariants);
  `validate_output` (reconciliation tie-out, lineage completeness, no-identity-merge and
  no-overwrite screens, reject completeness, prohibited-language screen, disclaimer). Each script
  ships a `--selftest` over bundled fixtures.
- **Evaluations:** trigger/routing (to `investment-reference-data-reviewer`,
  `investment-data-quality-reviewer`, `investment-data-quality-reviewer`,
  `investment-book-reconciler`, `fund-nav-control-reviewer`); a golden normalize case
  (5 canonical + 3 reason-coded rejects, same-security positions kept separate); deterministic
  script checks; a safety fixture (`canonical_noncompliant.json`) that fails closed on identity
  merge, source overwrite, broken reconciliation, prohibited language, and a missing disclaimer;
  and an external-delivery authorization check.
- **Handoffs:** downstream to the five adjacent Asset Management skills above; this skill
  normalizes shape only and does not duplicate their identity/value/reconciliation work.

### Pending before release
- Domain-SME (investment-data governance) + control-owner blind review; confirm the authoritative
  mapping-ruleset source, its owner, and the canonical-schema field list per record type.
- Confirm the canonical CSV column layout and lineage columns with downstream consumers.
- Wire read-only MCP integrations (custodian, administrator, OMS, accounting/GL, ruleset service)
  at deployment; the bundled scripts are deterministic validators/transformers over JSON schemas
  and de-identified fixtures, not live connectors.
