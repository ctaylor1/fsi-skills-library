# Changelog — claim-damage-evaluation-comparator

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic line-item comparison across a claim's damage documents — duplicates
  (double-counted across documents), differences (same item priced differently), and unsupported
  items (no linked support) — each cited; review-only disposition.
- **Controls:** R3 read-only; NEVER sets/values/recommends damages, reserve, or settlement, never
  determines coverage/liability, never approves payment; exact-normalized grouping only (no
  guess-merging); `external-delivery` approval; NPI/PII (incl. medical) masking.
- **Scripts:** `validate_input` (documents + line items, doc_id integrity), `calculate_or_transform`
  (normalize + group + flag), `validate_output` (citation coverage, review-only disposition,
  no-valuation screen, disclaimer).
- **Evaluations:** trigger/routing, golden findings (difference/duplicate/unsupported with
  normalization), missing-amount edge, deterministic script checks, no-valuation safety + injection,
  external-delivery authorization.
- **Handoffs:** `liability-evidence-matrix-builder`, `claim-settlement-authority-packet`.

### Pending before release
- Claims owner review; category-support and normalization-config sign-off.
- Wire read-only claims document/line-item MCP integrations at deployment.
