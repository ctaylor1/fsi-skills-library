# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — investment-reference-data-reviewer

## 2026-09-20 — Phase 1 development corrections (unreleased)

- Repaired bounded native methods and disclosed their supported scope; see domain-rules and schema.
- Added detached original-input reconstruction, finite-JSON hashing and rejection of unvalidated output fields.
- Revised synthetic fixtures and independent operation regressions; no production, professional or institutional acceptance claimed.


## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic security-master enrichment — join approved identifier and attribute
  observations across a ranked source hierarchy, draft PROPOSED enriched values with provenance,
  classify disagreements and data-quality issues, and emit a steward conflict queue. Draft-only;
  no creation, no identity resolution, no write to the master.
- **Enrichment field registry:** `currency`, `exchange`, `asset_class`, `maturity`, `coupon`,
  `rating`, `benchmark`, `issuer` (plus identifier schemes handled separately). Each field maps to
  exactly one disposition (agreed / conflicted / missing / absent).
- **Conflict taxonomy (deterministic):** `identifier_conflict`, `identifier_invalid`,
  `attribute_conflict`, `stale_value`, `missing_required`, `unpermitted_source` — each with a
  field, severity, candidate list, and steward-review flag (see
  `scripts/calculate_or_transform.py`). ISIN (Luhn) and CUSIP (mod-10) check digits are validated
  offline.
- **Tie-out invariants:** field dispositions account for every field (`residual == 0`); attribute
  proposals == agreed + conflicted; conflict-queue length == Σ counts by type; every proposal
  cites ≥1 approved source; no proposal exists for a conflicting/invalid identifier.
- **Controls:** R2; hard boundary against creating a security, resolving/merging identities, or
  writing the master (proposals are `status: "PROPOSED"` only); no source adjudication; no silent
  correction/suppression; no investment advice; versioned-config required/material fields,
  tolerance, and freshness window; `external-delivery` approval; segregation of duties between
  preparer and steward.
- **Idempotency:** `enrichment_id` derived from `entity/as_of + input_fingerprint` (SHA-256 of
  normalized inputs) with no timestamp/random component; identical inputs reproduce identical
  output.
- **Scripts:** `validate_input` (job schema, unpermitted-source / freshness warnings), the
  enrichment engine, `validate_output` (tie-outs, conflict taxonomy, provenance, identity
  boundary, proposed-only + no-creation/resolution and no-advice screens, idempotency,
  disclaimer). All stdlib-only with `--selftest`.
- **Evaluations:** trigger/routing, golden enrichment tie-out, clean-agree edge, deterministic
  script checks, no-creation/no-identity-resolution/no-advice safety on a non-compliant fixture +
  injection, and external-delivery authorization.
- **Handoffs:** upstream `research-source-indexer`, `investment-record-normalizer`;
  downstream `investment-data-quality-reviewer`, `investment-data-quality-reviewer`,
  `fund-valuation-oversight-reviewer`. Creating a security / resolving an identity is a human
  security-steward (data governance) action.

### Pending before release
- Domain SME (security-master / data governance) + control-owner blind review; SoD confirmation
  for preparer vs steward.
- Confirm the versioned source-hierarchy / required-material-field / freshness config source and
  its owner.
- Wire read-only MCP integrations (reference-data vendors, issuer/exchange filings, entity
  resolution) at deployment.
