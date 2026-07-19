# Changelog — model-validation-assistant

## [Unreleased]
- **Fix (guardrail, SR 11-7 independence):** the output guardrail derived the credited-`pass`
  independence gate from "has any citation", while the engine derived it from
  `independent_evidence` **and** an independent `source_ref`. The two definitions could diverge —
  false-rejecting valid reports and letting a non-independent `pass` (a citation drawn only from a
  test working paper) slip through. The engine now carries an explicit `independently_sourced`
  boolean on every area, and `validate_output` enforces both the credited-`pass` check and the
  deterministic tie-out against that same flag (missing/false fails closed), so the engine and the
  guardrail cannot diverge. Added safety fixture
  `evals/files/validation_report_nonindependent_pass.json` and eval `safety-nonindependent-pass`
  (`expect_exit: 1`) reproducing the exact non-independent-pass bypass; updated `controls.md`,
  `domain-rules.md`, and `SKILL.md` to match.

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to support
independent model validation and draft traceable validation findings for human adjudication,
separating validation testing from the model inventory, the risk assessment, the governed model
documentation pack, and the validation decision itself.

- **Scope:** independently assess the seven required areas — `conceptual_soundness`, `data`,
  `performance`, `outcomes`, `limitations`, `controls`, `monitoring`; credit a `pass` only where
  the validator holds independent evidence; generate open, cited findings with a deterministic
  severity; roll up the overall severity and a NON-decisional recommended disposition; and route
  to the correct approver. Draft-only; no system-of-record change; the validation outcome is
  emitted `pending`.
- **Controls:** R3; no approval/certification/clearance of a model for use; no final validation
  decision; no closing/resolving/waiving findings; no assembling/filing the governed documentation
  pack (that is `model-risk-documenter`); developer-attested-only claims earn no independent
  credit; every area cited; severity is deterministic (materiality x independent status);
  versioned `framework_version`.
- **Scripts:** `validate_input` (intake schema, all-seven-areas check, needs-data + independence
  warnings), the validation engine (independence rule, effective status, findings, overall
  highest-wins severity, approver routing, `pending` outcome), and `validate_output` (template
  fidelity, source mapping / no-unsupported-claim, deterministic tie-out,
  deficiency/not_tested-must-have-a-finding, approval discipline, autonomous-decision / filing /
  documentation-assembly language screen, standing note).
- **Evaluations:** trigger/routing, golden 7-area intake exercising validated passes, a
  failed-test deficiency, a developer-attested-only coverage gap, a not-tested outcomes gap, and
  Medium/High severities; deterministic script checks; guardrail safety fixture (missing areas +
  approved status + closed finding + prohibited language + missing standing note); and refusal
  cases (no approval, no fabricated independence, no finding closure, prompt injection, decision/
  filing authorization).
- **Handoffs:** upstream `model-inventory-maintainer` / model registry (model + tier) and
  `ai-evaluation-benchmark-builder` / evaluation harness (independent evidence); adjacent
  `model-risk-documenter` (documentation of record), `ai-risk-assessment-builder`,
  `model-change-impact-analyzer`, `data-quality-issue-investigator`, `data-lineage-documenter`,
  `ai-incident-investigator`.

### Pending before release
- Model-risk / second-line control-owner blind review; independence review (validation vs.
  development) and segregation-of-duty review (validation vs. documentation vs. approval).
- Confirm the model risk framework / validation standard, required-area set, materiality-to-
  severity mapping, and approver-routing source, owner, and versioning (`framework_version`).
- Wire read-only MCP integrations (model registry/inventory, data catalog, evaluation harness,
  agent/tool logs, template library, risk/issue system) at deployment.
