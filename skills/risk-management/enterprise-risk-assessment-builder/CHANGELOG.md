# Changelog — enterprise-risk-assessment-builder

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
controlled **draft** enterprise risk assessment that links risks, scenarios, controls,
residual ratings, indicators, owners, evidence, and treatment actions — separating assembly
(this skill) from the specialist component analyses upstream and from human adjudication and
any system-of-record change downstream.

- **Scope:** score inherent risk, take residual credit only from tested + evidenced controls,
  compute residual vs appetite, flag over-appetite risks needing treatment, and render the
  approved template. Draft-only; no write to the risk register.
- **Controls:** R3; no acceptance of a residual, no approval/finalization, no risk closure,
  no attestation sign-off, no filing/register write; control credit is fail-closed
  (untested/unevidenced controls earn none); unsupported assertions fail the output screen;
  versioned scoring/appetite/template config.
- **Scripts:** `validate_input` (assessment schema, effectiveness/appetite bands, 1–5
  likelihood/impact, unknown-control and completeness warnings), `calculate_or_transform`
  (deterministic inherent → control-credit → residual → appetite builder with internal
  invariant self-test), `validate_output` (template fidelity, residual tie-out, no
  unsupported assertions, treatment coverage, decision/closure/filing language screen,
  approvals recorded & pending, standing note).
- **Assets:** `assets/output-template.md` with the ten required sections.
- **Evaluations:** trigger/routing, golden 6-risk assessment exercising each residual/appetite
  disposition, deterministic script checks, a non-compliant-output safety check that must fail
  closed, prompt-injection and untested-control-credit refusals, and an approval-bypass
  authorization check.
- **Handoffs:** upstream from `risk-control-self-assessment-assistant`,
  `key-risk-indicator-monitor`, `operational-risk-event-analyzer`,
  `stress-test-scenario-designer`, `third-party-risk-assessor`, `concentration-risk-monitor`;
  downstream to human adjudication and (post-approval) `regulatory-exam-response-packager`,
  `audit-evidence-packager`, `regulatory-change-impact-analyzer`.

### Pending before release
- ERM control-owner + 2nd-line (Enterprise Risk Management) blind review; segregation-of-duty
  review (drafting vs. challenge vs. approval).
- Confirm the scoring/appetite/template config source, owner, and versioning contract.
- Wire read-only MCP integrations (risk register/GRC, control-testing, appetite/limits, KRI,
  loss-event, scenario, third-party inventory, finance/operational) at deployment.
