# Changelog — model-risk-documenter

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble an
audit-ready model / AI documentation and validation-evidence pack across the ten required
sections and route it for human adjudication, separating documentation assembly from independent
validation, inventory maintenance, and the approval / attestation decision.

- **Scope:** assemble and trace `purpose`, `methodology`, `data`, `performance`, `limitations`,
  `controls`, `monitoring`, `changes`, `approvals`, and `traceability`; map every section to a
  versioned, cited source artifact; surface untraceable or missing evidence and carried
  validation findings as open documentation findings; record only cited approvals; route to the
  correct approver by model tier. Draft-only; no system-of-record change; the attestation block
  is emitted `pending`.
- **Controls:** R3; no validation/approval/attestation/certification/deployment clearance; no
  documentation-complete or fitness-for-use determination; no closing/resolving/waiving
  findings; an unversioned artifact earns no citation credit (section becomes a gap); no false
  attestation (approvals recorded only where cited); versioned `template_version` /
  `framework_version`.
- **Scripts:** `validate_input` (intake schema, all-ten-sections check, needs-data / untraceable
  warnings), the pack assembler (section status from content + versioned citation + required
  coverage, carried + generated open findings, cited-approval recording, traceability/readiness
  roll-up, tier-based approver routing, `pending` attestation), and `validate_output` (template
  fidelity, source-to-document traceability tie-out, methodology/limitation coverage, finding
  discipline, no-false-attestation / finding-approval consistency, autonomous-decision language
  screen, standing note).
- **Evaluations:** trigger/routing, golden 10-section intake exercising documented / gap /
  needs-data sections plus a carried validation finding, deterministic script checks, a guardrail
  safety fixture (missing sections + closed finding + uncited approval + approved attestation +
  prohibited language + missing standing note → fail closed), and refusal cases (no attestation,
  no fabricated evidence, no false approval, prompt injection, close-findings authorization).
- **Handoffs:** upstream `model-inventory-maintainer` (tier), `model-validation-assistant`
  (results + findings), `ai-evaluation-benchmark-builder`, `data-lineage-documenter`, and the
  template library; adjacent `model-change-impact-analyzer`, `ai-risk-assessment-builder`,
  `data-quality-issue-investigator`, `prompt-and-agent-risk-reviewer`,
  `agent-permission-scope-reviewer`, `third-party-ai-due-diligence-assistant`,
  `ai-incident-investigator`; downstream adjudication by the model owner, independent validation,
  and the Model Risk Committee (human).

### Pending before release
- Model-risk control-owner + independent-validation blind review; segregation-of-duty review
  (documentation vs. validation vs. approval).
- Confirm the documentation template, required-coverage list, and approver-routing source, owner,
  and versioning (`template_version` / `framework_version`).
- Wire read-only MCP integrations (model registry, development/validation artifacts, data
  catalog/lineage, monitoring, controls/approval memos, template library, risk/issue system) at
  deployment.
