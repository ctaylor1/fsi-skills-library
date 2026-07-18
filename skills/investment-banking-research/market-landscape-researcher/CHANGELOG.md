# Changelog — market-landscape-researcher

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** map an industry/theme across value chain, competitors, customers, regulation,
  technology, economics, transactions, and strategic implications, as a source-linked draft.
- **Controls:** R2; no investment recommendation or advice; source-grounded claims only;
  MNPI handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic structuring of the
  landscape), `validate_output` (source/citation coverage, no-advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden landscape, deterministic script checks, no-advice
  safety, external-delivery authorization.
- **Handoffs:** upstream/lateral `market-sizing-builder`, `company-profile-builder`;
  downstream `investment-banking-pitch-builder`, `due-diligence-packager`.

### Pending before release
- Domain SME (sector/strategy) blind review; source-hierarchy sign-off.
- Wire read-only research/market-data MCP integrations at deployment.
