---
name: insurance-producer-compensation-reconciler
description: "Reconcile earned producer compensation from contractual earning triggers, commission bases, split shares and linked chargebacks. Use for compensation ledger breaks; no inferred commission rules, payment, licensing determination or fiduciary withdrawal."
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
  aws-fsi-owner: "Insurance distribution finance"
  aws-fsi-primary-user: "Producer compensation analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance Producer Compensation Reconciliation

The supported ledger records commission earned when the supplied contract trigger is evidenced. Gross earned commission = supplied commissionable base × contractual decimal rate. Allocate that gross across explicit producer shares summing to one. A chargeback references an earlier in-period earned event for the same policy and agreement and applies a supplied fractional reversal to the original gross and original split shares. Cumulative fractions cannot exceed one. Do not infer chargeback entitlement merely from cancellation.

One agreement rate applies per event, with effective dates, explicit earning trigger, premium basis and source evidence. Splits have their own source references. Reconcile net earned activity to reported producer amounts; this is neither cash accounting nor a payable balance roll-forward. Opening-period chargebacks, vesting disputes, changing split recipients, contingencies, fee schedules, rounding settlements and licensing/appointment judgments need additional reviewed methods. Arithmetic is unrounded Decimal; approved payout rounding is separate.

A complete ledger can contain known zero earned amounts. An absent amount, agreement or split is not zero. No payment, offset of fiduciary funds or agent communication follows from the draft.

## Prepare and review

Read [references/schema.md](references/schema.md) to construct native input and [references/source-map.md](references/source-map.md) to bind evidence. Do not invent facts to fill the schema or treat invented fixtures as approved rule profiles. The profile must establish jurisdiction, product, effective dates, method and accountable reviewer.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Save the output in an authorized location and run `python scripts/validate_output.py OUTPUT.json`. Output validation re-runs the native method from retained source evidence, including when someone has recomputed hashes after altering results. Use [assets/output-template.md](assets/output-template.md) for the human-readable draft, citing the actual source passages.

Read [references/domain-rules.md](references/domain-rules.md), [references/controls.md](references/controls.md) and [references/handoffs.md](references/handoffs.md) for limits and ownership. [references/insurance-foundation.md](references/insurance-foundation.md) and [references/insurance-contract.md](references/insurance-contract.md) define retained evidence, inherited unresolved issues and source-bound capacity mappings. A complete draft or consistent content hash proves neither source truth nor professional approval.

Run `python scripts/test_domain.py` and executable cases in [evals/evals.json](evals/evals.json). Planned natural-language evaluations are recorded separately and remain unrun until actually reviewed. Production use still needs domain, control and legal/compliance acceptance and privacy/retention configuration.
