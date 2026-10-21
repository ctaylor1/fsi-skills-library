# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — portfolio-characteristics-change-monitor

## Unreleased — Phase 1 integrity repairs

- Added complete original-input binding and reconstruction checks; native output does not authenticate sources or accept unreviewed extra fields.
- Repaired bounded calculation/input contracts and documented unsupported cases in references/phase1-contract.md.
- Updated synthetic golden fixtures and native evaluation commands; added cross-package behavioral regressions.

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (Wave 5 — 2026 industry expansion; baseline
status `new`). Analyze & review, R2, read-only.

- **Scope:** compare two approved portfolio characteristic snapshots (current vs prior) —
  active weights, ex-ante tracking error, effective duration, beta, factor exposures —
  compute prior→current drift, flag material drift beyond versioned attention bands, cite
  evidence, and emit a change-and-exception packet with a suggested review priority.
- **Changes/exceptions (deterministic):** per-characteristic delta vs band; `material` when
  strictly over band; `route_to_compliance` when a current value is at/near a supplied mandate
  reference; `not_evaluable` when a characteristic is present in only one snapshot (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R2; HARD BOUNDARY against rebalancing (direct/recommend/size/execute a trade),
  limit setting/modification, and breach adjudication; approved-snapshots-only input contract;
  deterministic priority mapping; standing disclaimer; `external-delivery` approval.
- **Routing:** any at/near-limit characteristic is handed off to `investment-mandate-reviewer`
  (the authoritative limit test); the packet never decides a breach itself.
- **Scripts:** `validate_input` (approved-snapshot + schema + date-order contract, evaluability
  warnings), drift engine, `validate_output` (evidence/citation completeness, deterministic
  priority tie-out, rebalancing/limit/breach language screen, disclaimer, mandatory routing
  handoff).
- **Evaluations:** trigger/routing, golden Elevated case, missing-mandate-reference edge,
  deterministic script checks, no-direction safety fixture (fails closed), unapproved-input
  safety fixture (fails closed), prompt-injection, external-delivery authorization.
- **Handoffs:** `investment-mandate-reviewer` (limit adjudication), `portfolio-exposure-analyzer`,
  `fund-liquidity-assessor`, `portfolio-performance-attributor`, `portfolio-rebalancing-assistant`,
  `investment-committee-memo-builder`, `portfolio-holdings-summarizer`.

### Pending before release
- Domain SME (risk analytics) + control-owner blind review; confirm the versioned drift-band
  config source and its owner.
- Confirm the approved risk/analytics snapshot system of record and its approval provenance.
- Wire read-only MCP integrations (risk/analytics snapshots, PMS/OMS positions & benchmark,
  reference data, mandate reference, config) at deployment.
