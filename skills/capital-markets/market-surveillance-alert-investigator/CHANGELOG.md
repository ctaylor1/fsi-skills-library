# Changelog — market-surveillance-alert-investigator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created as the
**investigation** step for market surveillance, separated from first-line triage
(`surveillance-alert-triager`) and from human adjudication (distinct entitlements, evidence
depth, and case states).

- **Scope:** consume an escalated trade- or e-comms surveillance alert; resolve entities and
  events; build a durable, fully cited evidence bundle (chronology, parties, amounts,
  indicators, linked cases); and emit a disposition **recommendation**. Read-only; every
  case-state transition is a *proposed* action via the approval broker.
- **Controls:** R3; no autonomous case closure, market-abuse determination, exoneration, or
  STOR/SAR filing; investigation requires triage provenance (fail closed otherwise);
  information-barrier / MNPI handling; versioned thresholds and evidence-strength bands.
- **Scripts:** `validate_input` (escalated-case schema; escalation-provenance, entity, and
  chronology checks; needs-data warnings), `calculate_or_transform` (chronology + documented
  indicators + evidence-strength → disposition recommendation, idempotent `MKT-SURV-<id>`
  case ids), `validate_output` (durable case_id, provenance, allowed recommendations only,
  every-item-cited, band tie-out, closure/determination/filing language screen, standing
  note).
- **Evaluations:** trigger/routing, a golden 5-case set exercising every disposition
  (refer / escalate / close-NFA / needs-data / possible-duplicate), deterministic script
  checks, a no-closure/determination/filing safety fixture that fails closed, prompt
  injection, market-abuse-determination refusal, and closure/provenance authorization checks.
- **Handoffs:** upstream `surveillance-alert-triager`; lateral/downstream
  `communications-compliance-reviewer`, `adverse-media-investigator`,
  `best-execution-reviewer`, `conflicts-of-interest-reviewer`, `sanctions-match-adjudicator`;
  adjudication (closure/determination/filing) is a human/MLRO action, not a skill.

### Pending before release
- Capital-markets surveillance control-owner + legal/compliance blind review;
  segregation-of-duty (triage vs. investigate vs. adjudicate) review.
- Confirm the surveillance threshold/band config source, owner, and versioning; calibrate
  indicator thresholds per instrument/asset class and jurisdiction pack.
- Wire read-only MCP integrations (surveillance case-mgmt, OMS/EMS, market data, comms
  archive, account context, prior cases) at deployment.
