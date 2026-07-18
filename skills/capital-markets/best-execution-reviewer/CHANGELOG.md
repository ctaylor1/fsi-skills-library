# Changelog — best-execution-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). R3 decision support:
findings + cited evidence + a suggested review disposition for the best-execution committee.
Read-only; no determination, no closure, no filing.

- **Scope:** deterministic best-execution review of a client-execution population against the
  firm's versioned policy — price vs benchmark, material price miss, arrival-to-execution
  speed, fill rate, explicit + implicit cost, off-policy venue, and undocumented exception —
  each finding explainable and evidenced (see `scripts/calculate_or_transform.py`).
- **Controls:** R3; `human-approval: required`. Hard boundary against any best-execution or
  compliance determination, exception/case closure or disposition, remediation instruction,
  and regulatory filing/amendment; versioned-policy thresholds only; false-positive prompts
  required; deterministic disposition tie-out.
- **Scripts:** `validate_input` (executions schema, evaluability warnings), the best-ex check
  engine, `validate_output` (evidence/citation completeness, recognized findings, deterministic
  disposition tie-out, R3 decision/closure/filing-language screen, disclaimer, fp_checks).
- **Evaluations:** trigger/routing, golden Escalate case (all seven findings), thin-population /
  missing-benchmark edge, deterministic script checks, no-determination safety on a
  non-compliant pack (fails closed) + injection refusal, and committee-adjudication
  authorization.
- **Handoffs:** downstream to `market-surveillance-alert-investigator` /
  `surveillance-alert-triager`, `transaction-reporting-quality-checker`,
  `fixed-income-pricing-reviewer`, `trade-confirmation-explainer`,
  `post-trade-settlement-monitor`, `trade-break-resolver`, and
  `communications-compliance-reviewer`; determination/filing is a human/committee handoff with
  no catalog skill.

### Pending before release
- Domain SME (best-execution committee / market-structure) + control-owner blind review;
  fairness review of the multi-factor weighting per client classification.
- Confirm the versioned best-execution policy config source (thresholds, approved-venue list,
  client-class weights) and its owner.
- Wire read-only MCP integrations (OMS/EMS, market & reference data, policy config,
  communications archive, post-trade/clearing) at deployment.
