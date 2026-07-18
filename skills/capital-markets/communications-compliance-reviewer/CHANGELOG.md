# Changelog — communications-compliance-reviewer

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** review a communication against communications-compliance rules — classify it,
  flag prohibited/promissory claims, missing disclosures, supervision/retention/off-channel
  gaps, and escalation needs — with cited evidence and a recommended disposition.
- **Controls:** R3; findings/evidence only for registered-principal adjudication; NEVER
  approves/clears/files a communication, grants principal approval, closes the review, or
  asserts a confirmed violation; deterministic prohibited-decision screen with a bad fixture
  that fails closed.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic rule/flag
  evaluation), `validate_output` (evidence/citation coverage, no-approval/no-determination
  screen, disclaimer).
- **Evaluations:** trigger/routing, golden review, deterministic script checks,
  no-approval/no-determination safety, human-adjudication authorization.
- **Handoffs:** downstream to `surveillance-alert-triager` (escalations) and a
  registered principal / supervision for adjudication.

### Pending before release
- Registered-principal + compliance control review; jurisdiction rule-pack sign-off.
- Wire read-only communications-archive / supervision MCP integrations at deployment.
