---
name: insurance-siu-investigation-assistant
description: "Prepare an SIU hypothesis and contradictory-evidence matrix, source-bound custody register and lawful investigation task plan after triage. Use for insurer investigation casework; no fraud verdict, covert collection, autonomous referral or claim denial."
license: MIT
compatibility: Python 3.10+; offline structured evidence only. No live connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 3"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Explicit reviewed jurisdiction and product profiles required; synthetic US-TEST is not a legal profile"
  aws-fsi-owner: "Insurance special investigations"
  aws-fsi-primary-user: "Authorized SIU investigator"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance SIU Investigation Review

This is post-triage investigation support. Form a falsifiable question and an explicit innocent alternative for each hypothesis. Map evidence with a written rationale to supports, contradicts or neutral; no additive suspicion score or fraud verdict is calculated. If contradictory evidence is absent, plan a task that tests the innocent alternative. Keep uncertainty and source reliability separate from whether evidence supports an allegation.

Evidence identifies its locator, description, supplied SHA256 digest, initial holder and named review of collection basis. Order custody events by timezone-aware timestamps, check holder continuity and unchanged supplied digest, and reject ambiguous simultaneous transfers or future custody records. A consistent supplied chain does not authenticate content, establish legal admissibility or prove lawful collection. Record a receipt/attestation transfer even if there was no later transfer.

Tasks identify hypothesis, linked evidence, owner, purpose, source-bound authority/privacy review and due date. Supported planning methods are supplied-record-review, authorized-specialist-interview and authorized-record-request. These labels describe a draft task, not a capability to contact, collect or execute. Covert access, surveillance, credential abuse and protected-characteristic fraud scoring are outside scope. Regulatory referral standards and deadlines must come from a current jurisdiction profile and qualified investigator; this package never files a referral or denies a claim.

## Prepare and review

Read [references/schema.md](references/schema.md) to construct native input and [references/source-map.md](references/source-map.md) to bind evidence. Do not invent facts to fill the schema or treat invented fixtures as approved rule profiles. The profile must establish jurisdiction, product, effective dates, method and accountable reviewer.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Save the output in an authorized location and run `python scripts/validate_output.py OUTPUT.json`. Output validation re-runs the native method from retained source evidence, including when someone has recomputed hashes after altering results. Use [assets/output-template.md](assets/output-template.md) for the human-readable draft, citing the actual source passages.

Read [references/domain-rules.md](references/domain-rules.md), [references/controls.md](references/controls.md) and [references/handoffs.md](references/handoffs.md) for limits and ownership. [references/insurance-foundation.md](references/insurance-foundation.md) and [references/insurance-contract.md](references/insurance-contract.md) define retained evidence, inherited unresolved issues and source-bound capacity mappings. A complete draft or consistent content hash proves neither source truth nor professional approval.

Run `python scripts/test_domain.py` and executable cases in [evals/evals.json](evals/evals.json). Planned natural-language evaluations are recorded separately and remain unrun until actually reviewed. Production use still needs domain, control and legal/compliance acceptance and privacy/retention configuration.
