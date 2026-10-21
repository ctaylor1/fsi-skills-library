# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — portfolio-performance-attributor

## Unreleased — Phase 1 integrity repairs

- Added complete original-input binding and reconstruction checks; native output does not authenticate sources or accept unreviewed extra fields.
- Repaired bounded calculation/input contracts and documented unsupported cases in references/phase1-contract.md.
- Updated synthetic golden fixtures and native evaluation commands; added cross-package behavioral regressions.

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** build/refresh a single-period performance attribution — arithmetic Brinson-Fachler
  allocation / selection / interaction effects plus a currency effect by segment, a currency
  roll-up, reconciliation of the bottom-up return to the official book of record, methodology
  documentation, and QA tie-outs — as a source-linked draft for review.
- **Controls:** R2; draft-only; no investment advice or recommendation; no forward-looking or
  guaranteed-performance claim; no GIPS-compliance assertion; no fabricated returns/weights;
  `external-delivery` approval (methodology sign-off + compliance/marketing review before use).
- **Scripts:** `validate_input` (intake schema, model check, needs-data / weight-sum / official-
  return warnings), `calculate_or_transform` (deterministic Brinson-Fachler effects, currency
  effect, effect totals, currency roll-up, effects + book-of-record reconciliation),
  `validate_output` (required sections, per-segment and effect-total tie-outs, citation coverage,
  approvals, no-advice / no-performance-claim / no-GIPS / no-delivery screen, draft status, standing
  note).
- **Evaluations:** trigger/routing, golden 5-segment attribution exercising allocation/selection/
  interaction/currency and the official reconciliation, deterministic script checks, non-compliant
  fixture (tie-out break + prohibited language) safety check, prompt-injection / fabrication / GIPS-
  and-performance refusals, and delivery authorization.
- **Handoffs:** downstream `investment-commentary-builder`, `fund-fact-sheet-builder`,
  `investment-committee-memo-builder`, `client-review-preparer`; upstream
  `portfolio-holdings-summarizer`, `portfolio-exposure-analyzer`, `investment-mandate-reviewer`;
  multi-period linking / factor attribution and the compliance/marketing review are human /
  quant-team handoffs.

### Pending before release
- Domain SME (performance measurement) blind review; performance-methodology and benchmark-policy
  sign-off; compliance/marketing (SEC Marketing Rule) review of any advertised output.
- Confirm the attribution `config` (model, tolerances) source, owner, and versioning.
- Wire read-only performance/risk-system, PMS/accounting, and market/index-data MCP integrations at
  deployment.

## Phase 4 — 2026-10-04

Added explicit specialist extension with source/chronology/coverage controls, independent arithmetic regressions, practitioner contract and review template. Earlier native schema and fixtures remain supported. Results remain supplied-unverified drafts.
