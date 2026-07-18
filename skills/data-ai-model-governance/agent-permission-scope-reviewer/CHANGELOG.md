# Changelog — agent-permission-scope-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** least-privilege review of an agent/skill permission manifest — each operation
  mapped across seven dimensions (need, data classification, least privilege / access mode,
  approval gate, audit logging, segregation of duties, revocation/recertification) — with
  cited findings and a recommended disposition. Read-only; no access decision, no
  entitlement action.
- **Rules (deterministic):** `LP-NEED-01`, `LP-WRITE-NOGATE`, `LP-CLASS-MODE`,
  `LP-CLASS-UNDECLARED`, `LP-LOG-OFF`, `LP-SOD-COMBO`, `LP-REVOKE-MISSING`, `LP-ENV-PROD`
  — each with an approved rule id, severity, and cited evidence (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R3; hard boundary against access decisions (approve/deny/clear) and
  entitlement actions (grant/revoke/provision), review closure, risk acceptance, and
  waiver/exception filing; versioned-policy rule set only; `human_adjudication_required`
  always true; `required` human approval.
- **Scripts:** `validate_input` (manifest schema, evaluability warnings), the rule engine,
  `validate_output` (approved-rule-id + evidence/citation completeness, deterministic
  disposition tie-out, autonomous-decision/approval-language screen, human-adjudication flag,
  disclaimer).
- **Evaluations:** trigger/routing, golden Remediate-before-approval case, not-evaluable
  edge, deterministic script checks, no-autonomous-decision safety + injection, human-
  adjudication authorization.
- **Handoffs:** downstream to IAM/GRC adjudication and risk-acceptance, and to
  `prompt-and-agent-risk-reviewer`, `ai-evaluation-benchmark-builder`, and model-inventory /
  model-risk-documentation skills.

### Pending before release
- Domain SME (IAM / AI governance) + control-owner blind review; segregation-of-duties model
  review.
- Confirm the versioned least-privilege policy source (rule set, thresholds, severity
  mapping) and its owner.
- Wire read-only MCP integrations (IAM/entitlement, data catalog, agent/tool logs, model
  registry, policy) at deployment.
