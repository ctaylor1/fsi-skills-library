# Changelog — coverage-gap-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger evidence traceability, explicit no-coverage-determination /
no-advice guardrails, and a deterministic review-priority mapping).

- **Scope:** explainable coverage gaps (needs vs. policy) + dual-cited evidence + suggested
  review priority. Read-only; no coverage/eligibility/claim determination, no advice, no
  transaction recommendation.
- **Gaps (deterministic):** missing_coverage, exclusion_match (with endorsement buy-back
  check), limit_shortfall, sublimit_shortfall, coinsurance_shortfall, deductible_burden,
  endorsement_gap — each explainable and evidenced (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against coverage/eligibility/claim determinations,
  adequacy verdicts, personalized advice, and purchase steers; versioned-config thresholds
  only; review prompts required; `external-delivery` approval.
- **Scripts:** `validate_input` (needs+policy schema, evaluability warnings), gap engine,
  `validate_output` (evidence + dual-citation completeness, deterministic priority tie-out,
  determination/advice-language screen, disclaimer, review prompts).
- **Evaluations:** trigger/routing, golden Elevated case, no-required-coverage edge,
  deterministic script checks, no-determination safety + injection, external-delivery
  authorization.
- **Handoffs:** `policy-document-explainer`, `policy-wording-comparator`,
  `premium-quote-comparator`, `policy-renewal-reviewer`, `claim-readiness-checker`,
  `claim-denial-appeal-helper`.

### Pending before release
- Domain SME (underwriting/product) + control-owner blind review; conduct/fairness review of
  the gap taxonomy and priority mapping.
- Confirm the versioned threshold/priority config source and its owner.
- Wire read-only MCP integrations (policy admin, document intelligence, needs/producer,
  reference data, config) at deployment.
