---
name: claim-recovery-case-reviewer
description: "Prepare a source-bound claim recovery case with rights, supplied limitation dates, preservation tasks and collection allocation across explicit loss interests. Use for subrogation, contribution or salvage follow-through; no legal rights verdict, demand, settlement or disbursement."
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
  aws-fsi-owner: "Insurance claims recovery"
  aws-fsi-primary-user: "Subrogation and recovery specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Claim Recovery Case Review

Review each supplied subrogation, contribution or salvage right independently: debtor, substantive policy/legal basis, reviewer, recoverable limit and a reviewed limitation date. The assistant does not derive standing, priority, tolling or limitation law. Days to the supplied date prioritize human preservation work; an elapsed date is not a verdict that the right expired.

Collections retain gross amounts and explicit costs, including zero. A reviewer must establish that cost deduction and this allocation method are permitted. The bounded convention allocates net collection pro rata to supplied loss-interest amounts for each right. Interests cover insurer, claimant and any other recipient separately. Net allocation cannot exceed total interests; gross cannot exceed the supplied recovery limit. Do not invent made-whole, deductible-first, common-fund or salvage ownership rules. Amounts remain unrounded for review; payment rounding/residual handling needs separate approval.

Tasks bind a right, named owner, source and due date. Surface a task after the supplied limitation date and preserve the unresolved issue. This workflow prepares case evidence, not demands, releases, settlements or disbursement instructions.

## Prepare and review

Read [references/schema.md](references/schema.md) to construct native input and [references/source-map.md](references/source-map.md) to bind evidence. Do not invent facts to fill the schema or treat invented fixtures as approved rule profiles. The profile must establish jurisdiction, product, effective dates, method and accountable reviewer.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Save the output in an authorized location and run `python scripts/validate_output.py OUTPUT.json`. Output validation re-runs the native method from retained source evidence, including when someone has recomputed hashes after altering results. Use [assets/output-template.md](assets/output-template.md) for the human-readable draft, citing the actual source passages.

Read [references/domain-rules.md](references/domain-rules.md), [references/controls.md](references/controls.md) and [references/handoffs.md](references/handoffs.md) for limits and ownership. [references/insurance-foundation.md](references/insurance-foundation.md) and [references/insurance-contract.md](references/insurance-contract.md) define retained evidence, inherited unresolved issues and source-bound capacity mappings. A complete draft or consistent content hash proves neither source truth nor professional approval.

Run `python scripts/test_domain.py` and executable cases in [evals/evals.json](evals/evals.json). Planned natural-language evaluations are recorded separately and remain unrun until actually reviewed. Production use still needs domain, control and legal/compliance acceptance and privacy/retention configuration.
