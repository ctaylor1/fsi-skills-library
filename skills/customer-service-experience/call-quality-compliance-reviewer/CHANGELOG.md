# Changelog — call-quality-compliance-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable quality/compliance rubric checks over a contact-center interaction
  transcript + cited evidence + a suggested QA disposition band. Read-only; no misconduct or
  regulatory-breach determination, no pass/fail that drives discipline, no action.
- **Checks (deterministic):** recording-consent disclosure, identity authentication,
  product required disclosures, prohibited language, fair-treatment/vulnerability, complaint
  acknowledgement, commitment capture, empathy/courtesy — each explainable and evidenced to
  a transcript turn or a scanned scope (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against agent-misconduct/regulatory-breach determination,
  disciplinary/HR action, and regulatory filing; versioned-rubric markers/lexicon only;
  considerations (benign-explanation prompts) required; `external-delivery` approval.
- **Scripts:** `validate_input` (transcript schema, evaluability warnings), rule engine,
  `validate_output` (evidence/citation completeness, deterministic disposition tie-out,
  determination/action/advice-language screen, disclaimer, considerations).
- **Evaluations:** trigger/routing, golden "Compliance review required" case, partial-
  transcript edge, deterministic script checks, no-determination safety + injection,
  external-delivery authorization.
- **Handoffs:** downstream to `complaint-resolution-assistant`, `service-recovery-assistant`,
  `vulnerable-customer-support-assistant`, `operational-risk-event-analyzer`,
  `communications-compliance-reviewer`, `customer-interaction-summarizer`; coaching
  delivery, HR/disciplinary action, and regulatory-reporting decisions are human handoffs.

### Pending before release
- Domain SME (QA/compliance standards) + control-owner blind review; fairness review of the
  marker sets and lexicon (no protected-class proxies).
- Confirm the versioned rubric/disposition config source, its owner, and effective-dated
  per-product disclosure requirements and jurisdiction packs.
- Wire read-only MCP integrations (transcript/CRM, case, complaint, approved-knowledge,
  rubric config) at deployment.
