# Changelog — comps-analysis-builder

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** build/refresh trading comps — sourced operating metrics, EV bridges, trading
  multiples, outlier/NM flags, peer summary statistics, implied-value cross-check, peer
  rationale, and QA tie-outs — as a source-linked draft for review.
- **Controls:** R2; draft-only; no recommendation/rating/price target; no fabricated
  metrics; peers only within the versioned selection criteria; MNPI handling;
  `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic multiples/EV
  bridges/statistics), `validate_output` (tie-outs, citation coverage, no-recommendation /
  no-delivery screen).
- **Evaluations:** trigger/routing, golden comps set, deterministic script checks,
  no-recommendation safety, external-delivery authorization.
- **Handoffs:** downstream `scenario-sensitivity-generator`, `investment-banking-pitch-builder`,
  `company-profile-builder`, `due-diligence-packager`.

### Pending before release
- Domain SME (research/coverage) blind review; peer-selection criteria sign-off.
- Wire read-only filings/market-data MCP integrations at deployment.
