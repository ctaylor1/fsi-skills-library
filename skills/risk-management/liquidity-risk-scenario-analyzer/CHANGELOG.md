# Changelog — liquidity-risk-scenario-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable institution/ALM liquidity stress metrics + cited findings + a
  deterministic assessment band + adjudication-ready Contingency Funding Plan proposals.
  Read-only; no liquidity determination, funding/collateral action, breach disposition, or filing.
- **Metrics (deterministic):** per-scenario stressed inflows/outflows by time bucket, cumulative
  funding gap, counterbalancing capacity after stressed haircuts, survival horizon, coverage ratio,
  and peak cumulative gap (see `scripts/calculate_or_transform.py`).
- **Findings:** `survival_horizon_breach` (CRITICAL), `coverage_ratio_breach` (HIGH), structural
  `funding_concentration` (MEDIUM); severity → band mapping (Within appetite / Watch / Elevated /
  Breach), each finding evidenced and cited.
- **Controls:** R3; hard boundary against regulated liquidity determinations, funding/collateral/
  limit actions, breach clearance/waiver, and regulatory filing (LCR/NSFR/2052a); versioned-config
  assumptions only; `required` human (Treasury/ALCO) approval.
- **Scripts:** `validate_input` (position/scenario schema, evaluability warnings), stress engine
  with a `--selftest` determinism + evidence self-check, `validate_output` (evidence/citation
  completeness, deterministic band tie-out, finding-to-number tie-out, regulated-decision/filing/
  closure screen, disclaimer, proposed-options requirement).
- **Evaluations:** trigger/routing, golden Breach case, within-appetite edge, deterministic script
  checks, no-decision safety + injection, adjudication authorization.
- **Handoffs:** upstream `stress-test-scenario-designer`, `cashflow-forecaster`; downstream
  `enterprise-risk-assessment-builder`, `management-reporting-packager`, `key-risk-indicator-monitor`,
  `regulatory-exam-response-packager`, `model-validation-assistant`; boundary with the buy-side
  `liquidity-stress-analyzer`.

### Pending before release
- Domain SME (treasury/ALM) + control-owner blind review; model validation of behavioral
  assumptions (runoff/rollover/inflow realization) and haircut add-ons.
- Confirm the versioned scenario/limit config source, its owner, and the jurisdiction packs.
- Wire read-only MCP integrations (ALM positions, collateral inventory, deposits/funding, market
  data, config) at deployment.
