---
name: disability-care-benefit-reviewer
description: "Review disability or long-term-care benefit criteria by period, qualified evidence, continuous calendar waiting periods, daily indemnity caps and policy offsets. Use for carrier or administrator benefit review; no diagnosis, medical adjudication, benefit decision or claimant appeal."
license: MIT
compatibility: Python 3.10+; offline structured evidence only. No live connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 3"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Explicit reviewed jurisdiction and product profiles required; synthetic US-TEST is not a legal profile"
  aws-fsi-owner: "Insurance disability and long-term-care claims"
  aws-fsi-primary-user: "Disability or LTC benefits analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Disability and Care Benefit Review

Map each policy-derived criterion to its responsible qualified role: medical, vocational or administrative. Retain supplied met/unmet/unknown observations and periods, including contrary evidence. Multiple different observations for one period/criterion remain conflicting. Every observation must cover the entire requested period; split periods where facts or policy definitions change. The assistant never determines disability, functional limitation, cognition or medical necessity.

The implemented scenario supports continuous calendar waiting days followed by a daily indemnity benefit. First potential benefit day = evidence-established onset + supplied whole waiting-day count. Benefit periods include both endpoints, cannot overlap and must be within as_of. Gross = eligible calendar days × min(supplied daily amount, daily cap), only where every criterion is evidenced met. Subtract explicit period offsets, floored at zero, then cap the aggregate by the supplied remaining benefit limit. Unknown offsets require a gap; a complete empty inventory means zero offsets. A supplied unmet criterion withholds the scenario and requires human review, never an automated denial.

This convention excludes service-day elimination periods, reimbursement-of-expense benefits, monthly income percentage calculations, partial-disability formulas, recurrent waiting credits and automatic offsets derived from public-benefit assumptions. A profile must explicitly select this supported method. An unsupported or invalid profile, case scope or benefit source withholds dependent waiting-period and local benefit arithmetic, not only the aggregate. Invalid period evidence withholds that period; invalid criterion or observation evidence withholds its gross benefit. An incomplete offset inventory leaves period offsets and net benefit unknown while independently supported gross benefit can remain visible. Use another reviewed method when the actual contract differs. Benefit eligibility and payment remain with qualified human adjudicators.

## Prepare and review

Read [references/schema.md](references/schema.md) to construct native input and [references/source-map.md](references/source-map.md) to bind evidence. Do not invent facts to fill the schema or treat invented fixtures as approved rule profiles. The profile must establish jurisdiction, product, effective dates, method and accountable reviewer.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Save the output in an authorized location and run `python scripts/validate_output.py OUTPUT.json`. Output validation re-runs the native method from retained source evidence, including when someone has recomputed hashes after altering results. Use [assets/output-template.md](assets/output-template.md) for the human-readable draft, citing the actual source passages.

Read [references/domain-rules.md](references/domain-rules.md), [references/controls.md](references/controls.md) and [references/handoffs.md](references/handoffs.md) for limits and ownership. [references/insurance-foundation.md](references/insurance-foundation.md) and [references/insurance-contract.md](references/insurance-contract.md) define retained evidence, inherited unresolved issues and source-bound capacity mappings. A complete draft or consistent content hash proves neither source truth nor professional approval.

Run `python scripts/test_domain.py` and executable cases in [evals/evals.json](evals/evals.json). Planned natural-language evaluations are recorded separately and remain unrun until actually reviewed. Production use still needs domain, control and legal/compliance acceptance and privacy/retention configuration.
