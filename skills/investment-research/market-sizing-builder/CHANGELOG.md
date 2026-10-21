# Changelog — market-sizing-builder

##0.2.0 —2026-10-20

- Phase1 critical input/evidence/partial-state repairs; see native contract.
- Full detached-original reconstruction rejects tampered, omitted and extra result fields; CLI requires --input.
- Strict shapes, calendar dates and finite financial values; supplied-only, unverified permissions/source truth and deployment acceptance limits remain explicit.
- Refreshed native golden result and executable commands; independent adverse-case suite in tools/test_ir_company_phase1.py. No new research engine, live connector or action authority.

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

## 2026-09-20 — Category ownership migration

- Moved from Investment Banking & Research to Investment Research; stable skill ID retained.
- Native method and information/publication controls unchanged. Path alias is registered.
