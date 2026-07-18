# Changelog — knowledge-answer-composer

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** informational, read-only composition of a source-grounded answer to a
  customer-service question from approved policies, product terms, procedures, and current
  service status, with citations and explicit uncertainty.
- **Triggers:** positive (policy/terms/how-to/service-status/answer-this-question); negative
  (advice, determination) with routing to adjacent skills.
- **Controls:** R1; no advice/recommendation and no coverage/eligibility/fraud/complaint/
  account determination (deterministic language screen), approved-and-in-effect sources only
  (governance + freshness + jurisdiction screens), no invented facts; external-delivery human
  approval.
- **Tools/data:** read-only approved-knowledge/product-terms, procedure-library, service-
  status, and CRM/case/complaint context; durable `answer_id`.
- **Scripts:** `validate_input.py` (schema, source governance/freshness/jurisdiction warnings,
  no-usable-source gap) and `validate_output.py` (claim grounding, citation coverage, source-
  fidelity screen, advice/determination screen, disclaimer presence).
- **Evaluations:** trigger/routing, golden normal + unanswered edge, deterministic script
  checks, no-advice/determination safety, prompt-injection, external-delivery authorization.
- **Handoffs:** downstream to `next-best-action-assistant`, `complaint-resolution-assistant`,
  `customer-interaction-summarizer`, `vulnerable-customer-support-assistant`, and the R4
  `omnichannel-case-orchestrator`.

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the answer format.
- Wire read-only MCP integrations (approved knowledge, product terms, procedure library,
  service status, case/complaint context) at deployment.
- With/without benchmark vs. no-skill baseline; plain-language reading-level check.
