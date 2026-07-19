# Changelog — ai-incident-investigator

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to investigate
AI/model/agent incidents (harmful, incorrect, unauthorized, biased, privacy, security,
resilience) as casework — separating investigation from detection/triage, remediation
ownership, and adjudication/closure (distinct entitlements, evidence depth, and case states).

- **Scope:** preserve evidence and build a durable case — cited chronology, implicated
  model/agent and parties, impact estimate, documented severity, candidate root-cause
  hypotheses, and routed remediation recommendations. Read-only; every disposition is a
  *recommendation* pending human adjudication.
- **Controls:** R3; no incident closure, root-cause determination, model exoneration/
  redeployment, or regulatory/breach notification; containment is a referral, not an action;
  `privacy`/`security`/`unauthorized` raise a severity floor; versioned severity/routing config.
- **Scripts:** `validate_input` (incident-bundle schema, needs-evidence warnings), investigation
  engine (chronology + parties + impact + deterministic severity + hypotheses + routing +
  recommendation), `validate_output` (durable case_id, cited evidence, allowed dispositions,
  severity tie-out, closure/determination/filing/redeployment-language screens, standing note).
- **Evaluations:** trigger/routing, golden 6-incident bundle exercising every disposition and
  the escalation floor, deterministic script checks, a fail-closed safety fixture (closure +
  determination + filing + redeployment language, uncited evidence, missing case_id), plus
  prompt-injection and notification-refusal and closure-authorization checks.
- **Handoffs:** downstream to `model-change-impact-analyzer`, `model-validation-assistant`,
  `model-risk-documenter`, `ai-risk-assessment-builder`, `prompt-and-agent-risk-reviewer`,
  `agent-permission-scope-reviewer`, `data-quality-issue-investigator`, `data-lineage-documenter`,
  `data-loss-prevention-incident-assistant`, `cyber-incident-response-coordinator`,
  `operational-resilience-reporter`, `operational-risk-event-analyzer`, `agent-audit-trail-reviewer`,
  `third-party-ai-due-diligence-assistant`; human handoffs to the AI governance / model risk
  committee and to legal/compliance/DPO.

### Pending before release
- AI governance / model-risk control-owner + legal (notification thresholds) blind review;
  segregation-of-duty review across triage / investigate / remediate / adjudicate.
- Confirm the severity + routing config source, owner, and versioning; confirm the incident
  taxonomy against the firm's AI/model-risk policy.
- Wire read-only MCP integrations (risk/issue, model registry, agent/tool logs, eval harness,
  data catalog/lineage, policy library) at deployment.
