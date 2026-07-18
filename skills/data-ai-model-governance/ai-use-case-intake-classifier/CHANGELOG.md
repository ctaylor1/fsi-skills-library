# Changelog — ai-use-case-intake-classifier

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). R3 decision-support: the skill
classifies a proposed AI/agent use case and recommends a governance path for **human adjudication**;
it never approves, exempts, waives, or closes a use case, and never makes the binding governance
decision.

- **Scope:** explainable intake risk factors + cited evidence + a deterministic governance tier,
  recommended governance path, and required review gates. Read-only; no decision, no closure.
- **Factors (deterministic):** regulated-decision, autonomous-action, customer/public-facing,
  special-category data, personal-data-at-scale, high-materiality, cross-border, third-party model,
  GenAI/agentic, prohibited-practice — each explainable and evidenced (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R3; hard boundary against binding governance decisions (approve/clear/exempt/waive/
  close/sign-off); versioned-ruleset thresholds only; conservative on submission-vs-catalog conflict;
  `human_adjudication_required` enforced; `required` human approval.
- **Scripts:** `validate_input` (intake schema, evaluability warnings), classification engine,
  `validate_output` (evidence/citation completeness, deterministic tier/path tie-out, no-decision
  language screen, human-adjudication flag, required-reviews, disclaimer).
- **Evaluations:** trigger/routing, golden High-tier case, not-evaluable edge, deterministic script
  checks, no-decision safety + injection, human-adjudication authorization.
- **Handoffs:** downstream to `ai-risk-assessment-builder`, `model-inventory-maintainer`,
  `prompt-and-agent-risk-reviewer`, `agent-permission-scope-reviewer`,
  `third-party-ai-due-diligence-assistant`, `ai-evaluation-benchmark-builder`,
  `model-validation-assistant` / `model-risk-documenter`.

### Pending before release
- Domain SME (AI/Model Risk Governance) + control-owner blind review; fairness review of the factor
  set and thresholds.
- Confirm the versioned ruleset (factors, thresholds, tier/path mapping) source and its owner, and
  the jurisdiction-pack list beyond the US default.
- Wire read-only MCP integrations (model registry, data catalog, AI-governance policy, evaluation
  harness, agent/tool logs) at deployment.
