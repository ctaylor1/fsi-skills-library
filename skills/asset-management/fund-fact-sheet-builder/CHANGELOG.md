# Changelog — fund-fact-sheet-builder

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
controlled, source-mapped **draft** fund fact sheet for a fund/share-class, separate from
performance calculation, exposure analysis, and commentary drafting.

- **Scope:** map figures to the fact-sheet template (fund summary, standardized net-of-fees
  performance, holdings, risk, fees, ESG), reconcile every numeric figure to its system-of-record
  value, render required regulatory disclosures, build a cited source index, and list open items
  and outstanding approvals. Draft-only; no distribution, return promise, advice, rating, or
  recommendation.
- **Controls:** R2; external-delivery approval posture; no unsupported assertions (uncited
  figures become open items, never section entries); source-to-output reconciliation (a figure
  that does not tie to source is an open item, never asserted); MNPI/embargoed content excluded
  from external sheets (information-barrier control); stale data and identity mismatches surfaced
  as open items; required disclosures rendered as cited controlled content; versioned template /
  required-approvals / required-disclosures config.
- **Scripts:** `validate_input` (intake schema, unsourced/undated/unreconcilable/MNPI/missing-
  disclosure warnings), the assembler `calculate_or_transform` (status assignment, numeric
  reconciliation ledger, MNPI exclusion, section-incomplete detection, disclosure rendering,
  approvals capture, deduplicated source index), and `validate_output` (required sections, no-
  unsupported-assertion + reconciliation + no-MNPI screens, disclosure and approval completeness,
  return-promise/advice/distribution language screens, draft status, standing note).
- **Assets:** `output-template.md` mirroring the canonical fact-sheet sections.
- **Evaluations:** trigger/routing, a golden 10-figure fact sheet exercising every status
  (included, stale, unresolved, unsupported, MNPI-restricted, reconcile break, section-incomplete)
  plus recorded and outstanding approvals and a reconciliation ledger, deterministic script
  checks, a non-compliant fixture that fails closed, and injection / reconciliation / return-
  promise / MNPI / distribution-authorization refusals.
- **Handoffs:** upstream from `performance-attribution-builder`, `portfolio-exposure-analyzer`,
  `liquidity-stress-analyzer`, `fund-commentary-drafter`; downstream/lateral to
  `investment-committee-memo-builder`, `due-diligence-questionnaire-responder`,
  `mandate-compliance-monitor`. Performance verification, compliance/marketing review,
  registered-principal approval, and external distribution are human / compliance-owned (no
  catalog skill performs them).

### Pending before release
- Performance-measurement (GIPS) + compliance/marketing (retail-communication standards) +
  registered-principal blind review; segregation-of-duty review (draft vs. verify vs. approve
  vs. distribute).
- Confirm the fact-sheet template, required-sections, required-approvals, and required-disclosures
  config source, owner, and versioning per jurisdiction.
- Wire read-only MCP integrations (performance system, PMS/OMS, risk analytics, market data,
  controlled-content library, entity resolution, document intelligence) at deployment.
