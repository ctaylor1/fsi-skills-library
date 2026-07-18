# Changelog — company-profile-builder

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
controlled, source-mapped **draft** company profile / strip page for investment-banking and
research use, separate from analysis, valuation modeling, and deck assembly.

- **Scope:** map facts to the profile template (business overview, KPIs, ownership,
  management, trading data, transactions), assign a deterministic status, build a cited
  source index, and list open items and outstanding approvals. Draft-only; no distribution,
  advice, rating, recommendation, or price target.
- **Controls:** R2; external-delivery approval posture; no unsupported assertions (uncited
  facts become open items, never section entries); MNPI excluded from external profiles
  (information-barrier control); stale market/filing data and identity mismatches surfaced
  as open items; versioned template / required-approvals config.
- **Scripts:** `validate_input` (intake schema, unsourced/undated/MNPI warnings), the
  assembler `calculate_or_transform` (status assignment, MNPI exclusion, section-incomplete
  detection, approvals capture, deduplicated source index), and `validate_output` (required
  sections, no-unsupported-assertion + no-MNPI screens, approval completeness, advice/rating
  and distribution/delivery language screens, draft status, standing note).
- **Assets:** `output-template.md` mirroring the canonical profile sections.
- **Evaluations:** trigger/routing, a golden 7-fact profile exercising every status
  (included, stale, unresolved, unsupported, MNPI-excluded, section-incomplete) plus recorded
  and outstanding approvals, deterministic script checks, a non-compliant fixture that fails
  closed, and injection / MNPI / advice / distribution-authorization refusals.
- **Handoffs:** downstream to `investment-banking-pitch-builder`, `coverage-meeting-preparer`,
  `due-diligence-packager`, `buyer-investor-list-builder`, `transaction-process-tracker`;
  upstream from `comps-analysis-builder`, `dcf-modeler`, `earnings-results-analyzer`,
  `market-landscape-researcher`. Advice/ratings, MNPI clearance, and external distribution are
  human / compliance-owned (no catalog skill performs them).

### Pending before release
- Research supervisory-analyst + compliance/control-room (information-barrier / MNPI) blind
  review; segregation-of-duty review (draft vs. approve vs. distribute).
- Confirm the profile template, required-sections, and required-approvals config source,
  owner, and versioning.
- Wire read-only MCP integrations (market/financial data, filings, research corpus, entity
  resolution, document intelligence, CRM, data room) at deployment.
