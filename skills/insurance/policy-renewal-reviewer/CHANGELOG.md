# Changelog — policy-renewal-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable expiring-vs-proposed renewal comparison + cited evidence + drafted
  renewal questions + suggested review disposition. Read-only; no renewal decision, no pricing,
  no bind, no notice, no coverage/claim determination, no personalized advice.
- **Findings (deterministic):** premium_change, exposure_change, limit_reduced,
  deductible_increased, coverage_removed, coverage_added, form_endorsement_change,
  loss_ratio_flag, large_open_claim, rate_exposure_divergence — each explainable and evidenced
  (see `scripts/calculate_or_transform.py`). Absent data is reported `not_evaluable`, never as
  "no change".
- **Controls:** R2; hard boundary against renewal/pricing/coverage determination, binding,
  non-renewal notice, and personalized advice; versioned-config thresholds only; context prompts
  required; `external-delivery` approval.
- **Scripts:** `validate_input` (both-terms/coverage/claim schema, evaluability warnings), findings
  engine, `validate_output` (evidence/citation completeness, deterministic disposition tie-out,
  determination/pricing/advice-language screen, disclaimer, context prompts).
- **Evaluations:** trigger/routing, golden Escalated case, missing-term and no-claims edges,
  deterministic script checks, no-determination safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `underwriting-workbench-assistant`, `policy-wording-comparator`,
  `coverage-gap-analyzer`, `claims-file-reviewer`, `catastrophe-exposure-monitor`,
  `premium-quote-comparator`, `policy-document-explainer`; renewal decision / pricing / bind / notice
  reframed as licensed-underwriter (human) actions.

### Pending before release
- Domain SME (underwriting/actuarial) + control-owner blind review; fairness review of findings and
  loss-history handling.
- Confirm the versioned threshold/disposition config source and its owner, and the filed-forms library
  binding for edition resolution.
- Wire read-only MCP integrations (policy administration, claims, forms library, config,
  actuarial/catastrophe) at deployment.
