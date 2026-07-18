# Changelog — ai-risk-assessment-builder

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to draft an
audit-ready AI/ML risk assessment across the ten required domains and route it for human
adjudication, separating assessment drafting from use-case intake, independent validation,
and the risk decision itself.

- **Scope:** score inherent and residual risk across `data`, `model`, `fairness`,
  `explainability`, `security`, `privacy`, `third_party`, `human_oversight`, `resilience`,
  and `monitoring`; map every risk statement to a cited source; surface open findings with
  recommended remediation; route to the correct approver. Draft-only; no system-of-record
  change; the approval block is emitted `pending`.
- **Controls:** R3; no approval/certification/risk-acceptance/deployment clearance; no final
  risk determination; no closing/resolving/waiving findings; unproven controls get no
  coverage credit; every domain cited; residual is deterministic (controls reduce
  likelihood, never impact; residual is never zero); versioned `framework_version`.
- **Scripts:** `validate_input` (intake schema, all-ten-domains check, needs-data warnings),
  the assessment engine (likelihood x impact matrix, coverage tiers, residual bands,
  findings, overall highest-wins rating, approver routing, `pending` approval), and
  `validate_output` (template fidelity, source mapping, residual/overall tie-out,
  High-residual-domain-must-have-a-finding, approval discipline, autonomous-decision language
  screen, standing note).
- **Evaluations:** trigger/routing, golden 10-domain intake exercising High/Medium residuals
  and every finding path, deterministic script checks, guardrail safety fixture (missing
  domains + approved status + prohibited language + missing standing note), and refusal cases
  (no approval, no fabricated evidence, prompt injection, close-findings authorization).
- **Handoffs:** upstream `ai-use-case-intake-classifier` (inherent tier), model registry, and
  `ai-evaluation-benchmark-builder` / `model-validation-assistant` (evidence); adjacent
  `prompt-and-agent-risk-reviewer`, `agent-permission-scope-reviewer`,
  `third-party-ai-due-diligence-assistant`, `data-lineage-documenter`,
  `data-quality-issue-investigator`, `ai-incident-investigator`, `model-inventory-maintainer`.

### Pending before release
- AI/model-risk control-owner + second-line blind review; segregation-of-duty review
  (drafting vs. validation vs. approval).
- Confirm the control framework / risk-domain taxonomy, matrix, and approver-routing source,
  owner, and versioning (`framework_version`).
- Wire read-only MCP integrations (model registry, data catalog, evaluation harness,
  agent/tool logs, template library, risk/issue system) at deployment.
