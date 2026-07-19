# Changelog — cyber-incident-response-coordinator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** maintain a single, source-linked cyber-incident **coordination record** —
  chronology, IR roles, evidence with chain of custody, decision log, containment/eradication/
  recovery tasks, communications, dependencies, and post-incident actions — with a **suggested**
  severity band and **notification reminders**. Read-only; no decision, action, closure, or filing.
- **Deterministic core (`scripts/calculate_or_transform.py`):** chronology ordering, role
  coverage, open/overdue tasks by phase, evidence custody completeness, decision status
  (pending vs. human-adjudicated), severity mapping (SEV1–SEV4) from the `impact` block, and
  notification reminders routed to named humans/skills.
- **Controls:** R3 decision-support; hard boundary against regulated decisions, official severity
  classification, response actions (revoke/isolate/patch/restore), incident closure, and
  breach/regulatory/SAR filing; versioned-config thresholds only; `required` human approval.
- **Scripts:** `validate_input` (record schema, custody/role/citation warnings), the coordination
  engine, `validate_output` (no autonomous decision/closure/filing language, no self-attributed
  executed response action (revoke/isolate/patch/restore/block/quarantine/contain/disable),
  record_status not closed/filed, terminal decisions need a human decided_by, deterministic
  severity tie-out, evidence/chronology citability, standing disclaimer).
- **Evaluations:** trigger/routing, golden SEV1 coordination case, thin-impact edge, deterministic
  script checks, and two fail-closed safety fixtures — autonomous closure + filing, and an
  otherwise-valid pack whose narrative claims the skill executed containment — each at `expect_exit 1`.
- **Handoffs:** upstream from `security-alert-triage-assistant`, `phishing-and-bec-investigator`,
  `data-loss-prevention-incident-assistant`; downstream/lateral to `identity-access-reviewer`,
  `vulnerability-prioritization-assistant`, `cloud-security-posture-reviewer`,
  `operational-resilience-reporter`, `third-party-cyber-risk-reviewer`, `ransomware-readiness-assessor`,
  `operational-resilience-scenario-tester`, `payment-fraud-case-investigator`,
  `suspicious-activity-report-drafter`; plus legal/privacy, executive crisis-management, and
  external DFIR human handoffs.

### Pending before release
- Domain SME (CISO / incident-commander) + control-owner blind review; legal/privacy review of the
  notification-reminder wording per jurisdiction.
- Confirm the versioned severity-mapping / mandatory-role config source and its owner.
- Wire read-only MCP integrations (incident management, SIEM/SOAR, IAM, posture, CMDB, threat
  intel, resilience register, config) at deployment.
