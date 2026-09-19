---
name: insurance-premium-audit-reviewer
description: "Reconstruct audited premium from source-bound exposures, classifications, manual versions, unit rates and modifiers; compare the reported audit and deposit. Use for end-of-period premium audits, without changing classifications, billing or coverage."
license: MIT
compatibility: Python 3.10+; offline structured evidence only. No live connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 3"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Explicit reviewed jurisdiction and product profiles required; synthetic US-TEST is not a legal profile"
  aws-fsi-owner: "Insurance premium audit and finance"
  aws-fsi-primary-user: "Insurance premium auditor"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance Premium Audit Review

The supported method computes each row as audited exposure / supplied unit size × supplied rate × supplied combined modifier. Sum unrounded rows, add the explicit fixed charge, apply the supplied minimum premium, then round once to cents using decimal half-up. Compare that result to the reported audit; subtract the deposit to show the audit adjustment. These are configurable method conventions, not a universal rating algorithm. Explicit zero minimum/charge is supported; absent values stay unknown.

Use one currency and one rate period covering the complete policy period. Every exposure requires a reviewed class mapping, exposure basis and source record; do not choose payroll inclusions, exclusions, overtime treatment, owner treatment or subcontractor rules. Use the applicable manual and supplied audit schedule to establish those facts. Midterm rate/classification changes, retrospective rating, tiered minimums and other assessment orders require a different method before calculating. A reconciliation break is not permission to bill.

Separate exposure verification, classification specialist review and finance approval. The result is a technical audit draft, never a coverage or classification decision.

## Prepare and review

Read [references/schema.md](references/schema.md) to construct native input and [references/source-map.md](references/source-map.md) to bind evidence. Do not invent facts to fill the schema or treat invented fixtures as approved rule profiles. The profile must establish jurisdiction, product, effective dates, method and accountable reviewer.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Save the output in an authorized location and run `python scripts/validate_output.py OUTPUT.json`. Output validation re-runs the native method from retained source evidence, including when someone has recomputed hashes after altering results. Use [assets/output-template.md](assets/output-template.md) for the human-readable draft, citing the actual source passages.

Read [references/domain-rules.md](references/domain-rules.md), [references/controls.md](references/controls.md) and [references/handoffs.md](references/handoffs.md) for limits and ownership. [references/insurance-foundation.md](references/insurance-foundation.md) and [references/insurance-contract.md](references/insurance-contract.md) define retained evidence, inherited unresolved issues and source-bound capacity mappings. A complete draft or consistent content hash proves neither source truth nor professional approval.

Run `python scripts/test_domain.py` and executable cases in [evals/evals.json](evals/evals.json). Planned natural-language evaluations are recorded separately and remain unrun until actually reviewed. Production use still needs domain, control and legal/compliance acceptance and privacy/retention configuration.
