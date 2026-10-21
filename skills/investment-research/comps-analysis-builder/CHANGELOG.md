# Changelog — comps-analysis-builder

## 0.2.0 — 2026-10-20

- Require detached original input for native output validation; reconstruct every result and reject omissions, alterations and extra fields. Guard finite numbers, shapes, dates, domains and duplicates; validate before computation.
- P/E × EPS produces equity value per share directly: do not subtract debt/cash or divide by shares again. EV multiples use the explicit EV-to-equity bridge. Every included company needs explicit debt, cash, preferred and minority components; unknown values cannot become zero. Currencies must be normalized before comparison; future/invalid price dates fail validation. Stale data, thin peers and metric exclusions remain disclosed limitations.
- Regenerate synthetic positive and adversarial fixtures. Passing checks is not source authentication, professional acceptance or independent institutional assurance.


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

## 2026-09-20 — Category ownership migration

- Moved from Investment Banking & Research to Investment Research; stable skill ID retained.
- Native method and information/publication controls unchanged. Path alias is registered.

## 0.3.0 — 2026-10-20

Phase2 mode adds bank P/E, P/B and P/TBV; insurer P/E and P/B; REIT P/FFO and P/AFFO. Each peer must share the exact denominator definition, accounting/consolidation basis, historical period, currency and units. Nonpositive denominators and stale prices are excluded visibly; the configured minimum count gates the median. These are equity per-share ratios, with no EV bridge or assumption that FFO, book value or distributable capital has been normalized.
