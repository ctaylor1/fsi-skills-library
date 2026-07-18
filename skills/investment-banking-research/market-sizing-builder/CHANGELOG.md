# Changelog — market-sizing-builder

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** estimate TAM/SAM/SOM with transparent top-down and bottom-up methods, scenario
  ranges, a documented source hierarchy, and explicit uncertainty — as a draft for review.
- **Controls:** R2; no investment recommendation or advice; every input cited; assumptions
  and method shown; MNPI handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic top-down/bottom-up
  sizing + scenario ranges), `validate_output` (tie-outs, method/assumption provenance,
  no-advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden sizing, deterministic script checks, no-advice
  safety, external-delivery authorization.
- **Handoffs:** lateral `market-landscape-researcher`; downstream
  `investment-banking-pitch-builder`, `scenario-sensitivity-generator`, `due-diligence-packager`.

### Pending before release
- Domain SME (strategy/research) blind review; assumption-source sign-off.
- Wire read-only research/market-data MCP integrations at deployment.
