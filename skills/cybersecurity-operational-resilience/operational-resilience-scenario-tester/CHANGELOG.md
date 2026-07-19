# Changelog — operational-resilience-scenario-tester

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** a multi-step domain workflow that designs/ingests severe-but-plausible
  operational-resilience scenarios, tests observed recovery against each important business
  service's impact tolerance, measures dependency coverage, and assembles cited decision and
  recovery evidence with a suggested review disposition. Read-only; no determination, no
  sign-off, no filing, no closure.
- **Engine (deterministic):** severe-but-plausible rubric flags, impact-tolerance test
  (within / breach / not_evaluable + margin) for downtime and data loss, dependency-coverage
  ratio, decision-evidence completeness, recovery-evidence presence, and a documented
  Informational / Review / Escalate disposition mapping (see
  `scripts/calculate_or_transform.py` and `references/domain-rules.md`).
- **Controls:** R3 decision support; hard boundary against resilience/compliance
  determinations, self-assessment sign-off, attestation, regulatory filing/submission,
  register updates, and case/exercise closure; versioned-config thresholds only, effective-
  dated to `as_of`; `required` human adjudication.
- **Scripts:** `validate_input` (scenario-package schema + evaluability warnings), scenario
  engine, `validate_output` (recovery/citation completeness, complete-decision check,
  deterministic disposition tie-out, prohibited-conclusion-language screen, disclaimer,
  remediation-actions requirement — fails closed on a non-compliant pack).
- **Evaluations:** trigger/routing, golden Escalate case (SC-01 breach), not-evaluable edge,
  deterministic script checks, no-conclusion safety + injection, human-adjudication
  authorization.
- **Handoffs:** downstream to `operational-resilience-reporter` (reporting/registers),
  `cyber-incident-response-coordinator` (live incident), `service-recovery-assistant`
  (customer remediation), `ransomware-readiness-assessor`, and
  `third-party-cyber-risk-reviewer`; distinct from `stress-test-scenario-designer`.

### Pending before release
- Domain SME (operational resilience / business continuity) + control-owner blind review.
- Confirm the versioned rubric/tolerance/disposition config source and its owner.
- Wire read-only MCP integrations (register, CMDB, incident/BCP, SIEM/SOAR, IAM, cloud
  posture, threat intelligence, config) at deployment.
