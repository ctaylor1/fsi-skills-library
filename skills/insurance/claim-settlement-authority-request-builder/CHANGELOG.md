# Changelog — claim-settlement-authority-request-builder

## [0.2.0] — 2026-09-18
- Implemented Phase 1 domain correctness and explicit unknown-state handling described in current domain rules.
- Added the shared insurance evidence envelope and output hash/metadata validation; provenance remains supplied, not authenticated.
- Added executable boundary and independent output-mutation regressions, migrated native synthetic fixtures, and regenerated valid golden outputs.
- Clarified native handoff requirements, draft/review limits, actor capacity and revision identity. Production configuration/professional acceptance remains outstanding.


## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic settlement-authority *request* packet — total exposure (indemnity +
  expense), required authority tier + approver by matrix lookup, evidence index, and checklist
  completeness (incl. exceeds-matrix escalation); each item cited; review-only disposition.
- **Controls:** R3 draft-only; NEVER approves a settlement, grants/exercises authority, authorizes
  payment, or sets/re-estimates the amount; exceeds-matrix exposure escalated (never approved at
  top tier); `external-delivery` approval; NPI/PII masking; the named approver is a lookup, not a
  delegation.
- **Scripts:** `validate_input` (evaluation figures + matrix + checklist), `calculate_or_transform`
  (exposure + tier lookup + completeness), `validate_output` (exposure tie, gap citation coverage,
  review-only disposition, no-approval screen, disclaimer).
- **Evaluations:** trigger/routing, golden packet (exposure/tier/completeness), exceeds-matrix edge,
  deterministic script checks, no-approval safety (language + tie) + injection, external-delivery
  authorization.
- **Handoffs:** `liability-evidence-matrix-builder`, `claim-cost-reconciler`.

### Pending before release
- Claims owner review; authority-matrix and checklist config sign-off per line/jurisdiction.
- Wire read-only claim/evaluation + authority-matrix MCP integrations at deployment.
