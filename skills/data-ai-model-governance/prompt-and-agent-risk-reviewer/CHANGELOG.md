# Changelog — prompt-and-agent-risk-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** design-time risk review of an LLM agent/prompt configuration — cited findings
  against a versioned control catalog + a recommended risk rating and disposition. Read-only;
  no approval, risk acceptance, attestation, filing, or review closure.
- **Controls (deterministic):** prompt-injection exposure (untrusted-input-to-privileged
  path, injection-persistent memory), autonomous high-impact tool without approval,
  over-broad tool scope, missing output/DLP guardrail for sensitive data, missing
  prohibited-behavior guardrail, no instruction-source boundary, no fail-closed/escalation,
  no eval coverage, insufficient audit logging — each explainable and evidenced (see
  `scripts/calculate_or_transform.py` and `references/domain-rules.md`).
- **Controls posture:** R3; hard boundary against approval, risk acceptance, exception,
  attestation, filing, and review closure; versioned control-catalog severities/mapping only;
  undocumented controls treated as gaps (`data_gaps`); `required` human adjudication.
- **Scripts:** `validate_input` (agent-package schema, evaluability warnings), control engine
  (findings + rating + disposition), `validate_output` (evidence/citation/remediation
  completeness, deterministic rating + disposition tie-out, approval/closure-language screen,
  disclaimer + adjudication note).
- **Evaluations:** trigger/routing, golden Critical case, minimal-config `data_gaps` edge,
  deterministic script checks, no-approval safety + injection, human-adjudication
  authorization.
- **Handoffs:** downstream to `ai-risk-assessment-builder`, `agent-permission-scope-reviewer`,
  `ai-evaluation-benchmark-builder`, `agent-audit-trail-reviewer`, `ai-incident-investigator`,
  `model-change-impact-analyzer`; upstream from `ai-use-case-intake-classifier`.

### Pending before release
- Domain SME (AI security / model risk) + control-owner blind review; fairness/robustness
  review of the control catalog and severities.
- Confirm the versioned control-catalog source, its owner, and the rating/disposition mapping.
- Wire read-only MCP integrations (agent/prompt registry, control catalog, model/data
  catalog, logs/eval-harness, risk/issue systems) at deployment.
