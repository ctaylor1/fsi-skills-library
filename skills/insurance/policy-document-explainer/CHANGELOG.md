# Changelog — policy-document-explainer

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-no-changes`
relative to the AWS baseline; authored fresh here).

- **Scope:** informational, read-only plain-language explanation of a single insurance
  policy document, with every statement source-linked to a declarations line, section, or
  clause.
- **Triggers:** positive (explain my policy / this section / this exclusion / my
  deductible / my declarations); negative (coverage or claim-outcome determination) with
  routing to adjacent skills.
- **Controls:** R1; no coverage/eligibility/claim-decision determination and no advice
  (deterministic language screen), no wording invention, no policy/edition merging;
  external-delivery human approval.
- **Tools/data:** read-only policy-administration, claims, and document-intelligence, plus
  approved-source retrieval for filed forms/endorsements; durable `explanation_id`.
- **Scripts:** `validate_input.py` (schema, single policy/edition, effective-date order,
  citations, cross-reference and data-quality warnings) and `validate_output.py`
  (element citation coverage, element-type validity, explained-count tie-out,
  determination/advice language screen, disclaimer presence).
- **Evaluations:** trigger/routing, golden normal + multi-policy edge, deterministic
  script checks, no-determination/no-advice safety, prompt-injection, external-delivery
  authorization.
- **Handoffs:** downstream to `coverage-gap-analyzer`, `claim-readiness-checker`,
  `claim-denial-appeal-helper`, `premium-quote-comparator`, `policy-wording-comparator`.

### Pending before release
- Domain SME (underwriting/claims) + control-owner blind review; accessibility review of
  the plain-language output format.
- Wire read-only MCP integrations (policy administration, document intelligence, filed-form
  retrieval) at deployment.
- With/without benchmark vs. no-skill baseline.
