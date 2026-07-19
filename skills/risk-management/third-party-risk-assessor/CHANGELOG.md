# Changelog — third-party-risk-assessor

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). R3 regulated /
control decision-support skill: evidence + recommendations only, with mandatory human
adjudication.

- **Scope:** deterministic scoring of eight third-party risk dimensions (criticality,
  control evidence, concentration, subcontractors/fourth-party, data, resilience, financial
  condition, exit/contingency) + cited evidence per material finding + a suggested composite
  risk tier. Read-only; no vendor decision, no filing, no system-of-record write.
- **Dimension bands (deterministic):** Low/Moderate/High/Critical per versioned-config
  thresholds; a documented composite mapping (see `references/domain-rules.md` and
  `scripts/calculate_or_transform.py`). Missing dimensions are `not_evaluable`, never Low.
- **Controls:** R3; hard boundary against approving/rejecting/onboarding/renewing/
  terminating/risk-accepting a vendor, closing/filing the assessment, giving investment
  advice, or writing a system of record; versioned-config thresholds only; human-adjudication
  note and disclaimer required.
- **Scripts:** `validate_input` (schema + evidence-traceability warnings), the dimension
  scoring engine (`calculate_or_transform`, with `--selftest` consistency checks), and
  `validate_output` (evidence-per-finding, deterministic tier tie-out, prohibited
  decision/closure/filing screen, disclaimer, adjudication note). All Python stdlib-only,
  self-contained, `--selftest` on bundled fixtures.
- **Evaluations:** trigger/routing, golden Critical vendor case, missing-financials edge,
  deterministic script checks, prohibited-decision safety fixture (fails closed), injection
  safety, and adjudication authorization.
- **Handoffs:** downstream to `third-party-cyber-risk-reviewer`,
  `enhanced-due-diligence-packager`, `operational-resilience-scenario-tester`,
  `concentration-risk-monitor`, `operational-risk-event-analyzer`,
  `financial-spreading-assistant`, `contract-obligation-extractor`,
  `third-party-ai-due-diligence-assistant`, `enterprise-risk-assessment-builder`; upstream
  from `procurement-sourcing-assistant` and `risk-control-self-assessment-assistant`.

### Pending before release
- Domain SME (third-party-risk / ERM) + control-owner blind review; fairness review of the
  `elevated_risk_jurisdictions` list and dimension weightings.
- Confirm the versioned threshold/framework config source and its owner.
- Wire read-only MCP integrations (inventory, control evidence, risk register,
  finance/operational data, config) at deployment.
