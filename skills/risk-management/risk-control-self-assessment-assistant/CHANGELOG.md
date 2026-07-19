# Changelog — risk-control-self-assessment-assistant

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). A first-line RCSA
drafting copilot: score risks and controls, evidence-map the conclusions, challenge the
statements, and package a controlled RCSA draft for human adjudication.

- **Scope:** deterministic inherent scoring (impact × likelihood), evidence-gated control
  design/operating effectiveness, residual vs. appetite, statement/control challenges, and a
  remediation plan — assembled into `assets/output-template.md`. Draft-only; no GRC write.
- **Controls (R3):** never sign off, attest, self-certify, close, finalize, accept risk, or
  write the system of record; **no credited control conclusion without evidence** (downgraded
  to `Unsubstantiated`); residual is computed, not decided; required approvals (control owner,
  first-line sign-off, second-line challenge) recorded as `pending`; versioned methodology/
  appetite.
- **Scripts:** `validate_input` (RCSA schema, evidence-gap/owner-TBD warnings),
  `calculate_or_transform` (inherent/effectiveness/residual scoring, challenges, remediation
  aging, package assembly), `validate_output` (required sections, no unsupported assertions,
  residual tie-out, required-approvals-recorded, autonomous-decision language screen, standing
  note).
- **Evaluations:** trigger/routing, golden 5-risk RCSA exercising Effective / Partially
  Effective / Unsubstantiated / no-control paths and overdue vs. unplanned remediation,
  deterministic script checks, non-compliant-package safety failure (exit 1), and refusals for
  sign-off/attestation, unevidenced crediting, residual tampering, and risk acceptance.
- **Handoffs:** feeders `operational-risk-event-analyzer`, `key-risk-indicator-monitor`,
  `third-party-risk-assessor`; downstream `enterprise-risk-assessment-builder`,
  `policy-procedure-gap-analyzer`, `audit-evidence-packager`, `board-committee-pack-builder`;
  independent challenge, sign-off, remediation ownership, and GRC finalization to humans.

### Pending before release
- ERM control-owner + second-line operational-risk blind review; three-lines segregation review.
- Confirm the RCSA methodology, rating scale, and risk-appetite source, owner, and versioning.
- Wire read-only MCP integrations (GRC register, assurance/testing, loss events, KRIs,
  third-party inventory, finance/operational data) at deployment.
