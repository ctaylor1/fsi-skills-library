# Changelog — model-change-impact-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable change-impact findings across eight dimensions (scope, data, tools,
  behavior, controls, testing, users, regulatory) + cited before/after evidence +
  deterministic impact band + recommended revalidation scope and governance path. Read-only;
  R3 decision-support, no autonomous change decision.
- **Dimensions & flags (deterministic):** each declared dimension evaluated with typed
  `risk_flags`; critical flags (`control_weakened`, `oversight_removed`,
  `autonomy_increased`, `regulatory_surface_changed`, `threshold_loosened`) force the
  Critical band. Undeclared dimensions are `not_evaluable`, never assumed unchanged
  (see `scripts/calculate_or_transform.py`).
- **Controls:** R3; mandatory human adjudication (`aws-fsi-human-approval: required`); hard
  boundary against approving, deploying, waiving revalidation for, closing, or attesting a
  change; versioned-config banding only; adjudicator prompts required.
- **Scripts:** `validate_input` (change-record schema, evidence-mandatory, evaluability
  warnings), change-impact engine with self-check, `validate_output` (evidence/citation
  completeness, deterministic band tie-out recomputed with the same versioned banding config
  the engine used — carried on `pack.config`, not hard-coded thresholds — scope-mapping
  tie-out, prohibited-decision screen, disclaimer, adjudicator prompts).
- **Evaluations:** trigger/routing, golden Critical case, no-change Low edge, deterministic
  script checks, prohibited-decision safety + injection, adjudication-required authorization.
- **Handoffs:** downstream to `model-validation-assistant`, `ai-evaluation-benchmark-builder`,
  `model-risk-documenter`, `model-inventory-maintainer`, `ai-risk-assessment-builder`,
  `data-lineage-documenter`, `data-quality-issue-investigator`,
  `prompt-and-agent-risk-reviewer`, `agent-permission-scope-reviewer`; upstream from
  `ai-use-case-intake-classifier` and `regulatory-change-impact-analyzer`.

### Pending before release
- Domain SME (model risk governance) + independent-validation blind review; fairness review
  of threshold-change handling under ECOA/Reg B.
- Confirm the versioned banding/mapping config source and its owner.
- Wire read-only MCP integrations (model registry, data catalog, evaluation harness,
  agent/tool logs, policy/controls, risk/issue tracking) at deployment.
