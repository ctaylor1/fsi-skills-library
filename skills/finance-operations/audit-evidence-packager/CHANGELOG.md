# Changelog — audit-evidence-packager

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
controlled, reviewer-ready **draft** audit evidence package from a PBC / evidence-request list —
separating evidence *packaging* (this skill) from the *testing and attestation* that consume it
(distinct entitlements, and the auditor's conclusion vs. a preparer's assembly).

- **Scope:** collect, index, redact, cross-reference, and quality-check requested evidence while
  preserving chain of custody and approval history; assign a deterministic packaging-readiness
  status; build an open-items register and a custody/redaction log; render the package document.
  Draft-only; no system-of-record change.
- **Controls:** R2; `external-delivery` approval. Never concludes on control operating
  effectiveness, issues/implies an audit opinion, signs a management representation, delivers/
  submits the package, fabricates/infers evidence, or over-redacts. Readiness states limited to
  `packaged-complete`, `evidence-gap`, `evidence-stale`, `redaction-required`, `custody-gap`,
  `needs-data`, `not-applicable`. Redaction outranks custody outranks staleness; `delivered_to_auditor`
  and `management_assertion_made` are always false.
- **Scripts:** `validate_input` (request/artifact-catalog schema, custody + redaction + mapping
  warnings), `calculate_or_transform` (deterministic packaging engine: mapping, redaction
  enforcement, custody check, period coverage, open-items register, custody log, rendered
  document), `validate_output` (template fidelity, completeness / no-unsupported-claims incl.
  chain-of-custody tie-out, redaction integrity, no conclusion/opinion/attestation/delivery
  language, required approvals, standing note). Each supports `--selftest` on a bundled fixture.
- **Assets:** `assets/output-template.md` — the eight required package sections (headers verbatim).
- **Evaluations:** trigger/routing, golden 8-request package exercising every readiness status,
  deterministic script checks, a non-compliant `package_bad.json` safety fixture (`validate_output`
  exits 1), plus no-conclusion / no-external-send / no-PII-leak refusals, and a delivery/attestation
  authorization refusal.
- **Handoffs:** upstream/lateral producers `gl-reconciler`, `financials-normalizer`,
  `month-end-close-orchestrator`, `regulatory-reporting-data-validator`, `pci-dss-evidence-assistant`;
  downstream consumers `financial-statement-audit-assistant`, `management-reporting-packager`,
  `risk-control-self-assessment-assistant`, `policy-procedure-gap-analyzer`. Testing, the audit
  opinion, and the management representation are human/auditor actions.

### Pending before release
- Finance & Controllership control-owner + internal-audit blind review; segregation-of-duty review.
- Confirm the remediation config source, owner, and versioning; confirm the audit-evidence
  retention policy and redaction/custody logging standard.
- Wire read-only MCP integrations (GRC/audit-workpaper + evidence repository, ERP/GL, subledgers,
  consolidation, FP&A, regulatory reporting, document-intelligence redaction, case-management
  custody) at deployment.
