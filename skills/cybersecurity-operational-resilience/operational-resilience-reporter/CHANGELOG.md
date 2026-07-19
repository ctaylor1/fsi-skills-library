# Changelog — operational-resilience-reporter

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). A Draft & package
(R3) skill that maintains critical-service and critical-third-party register packs and
assembles DRAFT operational-resilience reports (incident, testing, dependency,
impact-tolerance, self-assessment) from approved registers and versioned jurisdictional
templates.

- **Scope:** resolve service/third-party identity, compute deterministic facts (incident
  chronology, impact-tolerance breach, register completeness, third-party concentration),
  and fill every required template section with evidence-cited facts or an honest `gap`.
  Draft-only; no system-of-record change.
- **Controls:** R3; never files/submits to a regulator, attests/certifies, makes a
  resilience/compliance determination, closes a matter, or writes a register/incident/test
  system of record. Required human approvals (`accountable-executive`, `second-line-review`)
  are recorded, not granted. Versioned ruleset/template contracts; jurisdiction/template
  mismatch fails closed.
- **Scripts:** `validate_input` (dataset schema, identity/completeness warnings), report
  assembler (`calculate_or_transform`: deterministic facts + section fill), `validate_output`
  (template fidelity, no unsupported claims, impact-tolerance tie-out, required approvals,
  no-filing/no-attestation/no-determination language screen, draft watermark + standing note).
- **Assets:** `assets/output-template.md` (draft report template with required sections,
  tie-out table, approvals block, standing note).
- **Evaluations:** trigger/routing, golden self-assessment fixture (UK-PRA-SS1-21) exercising
  every required section, deterministic script checks, a non-compliant output fixture that
  fails closed, no-filing/no-fabrication safety, and an attestation-authorization refusal.
- **Handoffs:** upstream `operational-resilience-scenario-tester`,
  `cyber-incident-response-coordinator`, `operational-risk-event-analyzer`,
  `third-party-cyber-risk-reviewer`, `third-party-risk-assessor`; downstream/adjacent
  `board-committee-pack-builder`, `regulatory-exam-response-packager`,
  `audit-evidence-packager`, `regulatory-change-impact-analyzer`. Filing/attestation/
  notification are human handoffs (no skill).

### Pending before release
- CISO / operational-resilience control-owner + second-line and legal review of the language
  and determination screens.
- Confirm the jurisdictional rule pack + template source, owner, and versioning per
  deployment (UK-PRA-SS1-21, EU-DORA, US-INTERAGENCY packs).
- Wire read-only MCP integrations (registers, CMDB, incidents, tests, contracts, ruleset) at
  deployment.
