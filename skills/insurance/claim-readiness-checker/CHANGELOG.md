# Changelog — claim-readiness-checker

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger evidence, deadline/chronology, and no-coverage-decision
guardrails).

- **Scope:** explainable readiness checks + cited evidence + a `Ready` / `Ready with minor
  gaps` / `Not ready` status. Read-only; no coverage/eligibility/claim decision, no claim
  action.
- **Checks (deterministic):** required-documents-present, required-forms-valid (signed +
  accepted version), required-fields-complete, chronology-consistent (loss in policy period,
  loss ≤ reported ≤ prepared), deadlines-status (missed hard / at-risk) — each explainable and
  evidenced (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against coverage/eligibility/settlement/fraud determination
  and claim adjudication (approve/deny/close/settle/price/pay); versioned-config required-item
  and deadline catalogs only; considerations required when gaps exist; `external-delivery`
  approval.
- **Scripts:** `validate_input` (manifest/date/deadline schema, evaluability warnings), the
  readiness engine, `validate_output` (evidence-citation completeness, gap traceability,
  deterministic status tie-out, coverage/claim-decision-language screen, disclaimer,
  considerations).
- **Evaluations:** trigger/routing, golden Not-ready case, missing-dates edge, deterministic
  script checks, no-coverage-decision safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `claims-triage-assistant`, `claims-file-reviewer`,
  `claim-denial-appeal-helper`, `coverage-gap-analyzer`, `policy-document-explainer`,
  `claims-fraud-referral-assistant`.

### Pending before release
- Domain SME (claims handling) + control-owner blind review; fairness review of checks.
- Confirm the versioned required-item / deadline / threshold config source and its owner per
  claim type and jurisdiction.
- Wire read-only MCP integrations (policy administration, claims, document intelligence,
  config) at deployment.
