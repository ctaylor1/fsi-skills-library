# Asset management implementation plan

Approved scope: the September 20, 2026 architecture review and the subsequent three
architecture decisions. Phases 1–3 are authorized; Phase 2 was requested on September 21, 2026
and Phases 3 and 4 on October 4, 2026. Package presence does not imply
professional or deployment acceptance.

## Phase 1 — structure and correctness

- Record a disposition and accountable owner for all 30 original AM packages.
- Establish the asset-management index, router, support matrix and capability manifest.
- Create a first-class investment-research category; move reusable research there and
  retain transaction workflows under investment-banking. Preserve names where possible.
- Move source indexing/record normalization to Data, AI & Model Governance; move
  credit terms/surveillance to Investment Research.
- Merge quality/vendor comparison and proxy evidence/policy entrypoints, preserving
  independently testable methods. Keep exposure/risk, commentary/factsheets,
  monitoring/rebalancing, cash/liquidity and accounting/NAV review distinct.
- Repair demonstrated mandate, exposure, precision, temporal-evidence, approval,
  source-binding and audience-isolation defects in existing methods. Explicitly mark
  unsupported methods and jurisdiction profiles; do not fill missing facts.
- Establish detached source binding, versioned artifact/handoff and engine contracts,
  and generated portable resources from canonical shared sources.
- Preserve catalog regeneration, rename/path aliases, downstream references and
  isolated package operation. Do not copy another professional skill into a bundle.
- Test numerical and semantic regressions, source tampering, applicability, historical
  evidence, restricted information, explicit unknowns and typed receiver validation.

### Exit criteria

1. Every original package has a cataloged disposition and supported-scope statement.
2. Renamed/moved identifiers resolve without duplicate active workflow ownership.
3. Structural/package checks and meaningful independent regression cases pass.
4. Handoffs retain identity, units, evidence, unknowns and unresolved issues, and invoke
   the real receiver validator. Unsupported mappings fail explicitly.
5. Original-input validation binds all outcome-relevant inputs without authenticating
   them or exposing raw source snapshots in outward-facing artifacts.
6. Draft, technical validation, professional approval and execution remain separate.
7. Remaining method, data, jurisdiction and institutional acceptance gaps are recorded.

## Phase 2 — foundational business coverage (authorized 2026-09-21)

Add product/economics/distribution/client workflows; institutional policy/allocation/
construction and rebalancing; authoritative performance measurement; fund accounting;
investor operations; ETF/index foundations; private investment diligence/monitoring,
capital activity, waterfalls, performance and commitment pacing; institutional solutions;
investment-specific quantitative research. Add independently checked method references
and representative end-to-end cases. Basic ETF and private-market coverage belongs here.

### Phase 2 implementation scope and exit criteria

Add 29 foundations: B01/B02/B03/B05/B08, R04–R07, C01/C03/C04/C06/C07/C09,
K08/K11, O02/O05/O06/O07, S01–S05/S07, G01/G02. Expand B04 proposals,
R02 committee modes and R03 institutional manager diligence while preserving legacy
native interfaces. Each package requires a useful bounded method, documented inputs,
source/time/audience controls, detached output reconstruction, independent expected
cases, portable resources and explicit engine/unsupported boundaries. Update the
router, native adapter registry, catalog/support matrix and real handoff tests.
Preserve original Phase 1 evidence and record fresh independent forward evaluations.

Implementation record: [Phase 2 delivery](PHASE2-IMPLEMENTATION.md) and
[validation evidence](phase2-validation/README.md). The bounded implementation covers
the enumerated 29 new foundations and three expanded packages.

This foundation uses supplied institutional policies and accepted engine interfaces;
it does not install production systems, authenticate licenses or certify results as
system-of-record. That checkpoint left six specialized additions (C08/K07/S06/S08/S09/G05)
and four modernization adapters (T03–T06) for later phases.

## Phase 3 — modernization (authorized 2026-10-04)

Use shared architecture, workflow-automation, data-value and operations-analysis
capabilities for AM-specific data/platform/operating-model/AI adapters. Add licensed
connectors, point-in-time history, actual permission verification, observability,
parallel-run/cutover/recovery and controlled model/tool evaluations. Applicable market
structure and regulatory deadlines take priority over phase labels.

Library implementation: four AM adapters reuse the actual pinned shared architecture,
data-value, automation and operations methods, with detached native reconstruction.
An optional read-only HTTPS gateway client performs fresh request-bound permission
checks against a separately provisioned, approved institutional gateway. Point-in-time
sample resolution, per-grain migration reconciliation, replay/recovery chronology,
operating controls and supplied model/tool evaluations are implemented. No gateway,
vendor account, institutional identity or approved production model was provided;
live entitlement/license and real-model acceptance therefore remain deployment gates.
See [Phase 3 delivery](PHASE3-IMPLEMENTATION.md) and [validation](phase3-validation/README.md).

## Phase 4 — specialized extensions (authorized 2026-10-04)

Extend methods for complex derivatives, advanced fixed-income/factor/currency attribution,
advanced systematic research, specialized ETF baskets, private secondaries/continuation
funds, financing, real assets, institutional liabilities and jurisdiction profiles.
Tokenized-fund operations use the distinct legal-register/token/wallet/custody reconciliation job; they do not duplicate fund dealing or authorize token transfers.

Delivery adds six packages (C08, K07, S06, S08, S09, G05) and six explicit specialist extensions, bringing AM to 64 bounded packages including the router. The expanded methods preserve earlier input schemas and examples. See [Phase 4 delivery](PHASE4-IMPLEMENTATION.md) and [validation](phase4-validation/README.md). Institutional acceptance remains open below.

## Acceptance layers

Package validation, deterministic calculation tests, source fidelity, routing/handoff
tests, real-model evaluations and institutional specialist acceptance are independent
gates. Synthetic/reconstruction checks cannot establish source truth, licensed access,
professional judgment or production readiness. No release, main merge or execution
capability is implied by this implementation authorization.
