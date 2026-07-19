# Changelog — policy-procedure-gap-analyzer

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic mapping of internal policy/procedure controls to authoritative
  requirements, producing explainable findings + cited evidence + remediation
  recommendations. Read-only; no compliance determination, attestation, closure, or filing.
- **Findings (deterministic):** `coverage_gap` (no active mapped control), `parameter_conflict`
  (control weakens a requirement bound via versioned comparators — retention minimum,
  reporting-threshold maximum, training-interval maximum), `evidence_gap` (expected evidence
  pointer missing), `version_drift` (control cites a superseded requirement version → obsolete
  steps), `stale_review` (control past the review-cycle window). See
  `scripts/calculate_or_transform.py`.
- **Severity/priority (deterministic):** base severity by finding type, one-band drop for
  guidance-level requirements; `remediation_priority` derived from severity counts. Not-yet-
  effective/inapplicable requirements are informational; unmatched parameter kinds are
  `not_evaluable`. Documented in `references/domain-rules.md`.
- **Controls:** R3; hard boundary against compliance determination/attestation, finding
  closure, remediation sign-off, and regulatory filing/submission; versioned-config
  comparators and mapping only; standing disclaimer required; human adjudication `required`.
- **Scripts:** `validate_input` (requirement/control schema, evaluability warnings), the gap
  engine, `validate_output` (evidence/citation completeness, deterministic severity + count +
  priority tie-out, determination/closure/filing-language screen, disclaimer).
- **Evaluations:** trigger/routing, golden Priority-1 case (High:3/Medium:3/Low:1), not-in-
  effect edge, deterministic script checks, no-determination safety + injection, and a
  human-adjudication authorization check.
- **Handoffs:** upstream `regulatory-change-impact-analyzer`, `contract-obligation-extractor`;
  downstream `policy-document-assistant`, `regulatory-exam-response-packager`,
  `audit-evidence-packager`, `risk-control-self-assessment-assistant`,
  `enterprise-risk-assessment-builder`.

### Pending before release
- Domain SME (compliance/policy governance) + control-owner blind review; legal review of
  the paraphrased requirement citations.
- Confirm the versioned comparator/review-window/severity-mapping config source and its owner.
- Wire read-only MCP integrations (regulatory corpus, policy library, records archive,
  config) at deployment.
