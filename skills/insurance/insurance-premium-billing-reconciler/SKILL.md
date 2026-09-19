---
name: insurance-premium-billing-reconciler
description: "Reconcile an insurance account gross premium receivable from opening balances through invoices, adjustments, cash, refunds, writeoffs and linked full reversals; distinguish invoice aging and unapplied cash. Use for billed-premium and collection breaks; no posting, collection action, lapse decision or cancellation."
license: MIT
compatibility: Python 3.10+; offline structured evidence only. No live connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 2"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Explicit reviewed jurisdiction and product profiles required; synthetic US-TEST is not a legal profile"
  aws-fsi-owner: "Insurance policy administration and finance"
  aws-fsi-primary-user: "Insurance billing and finance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance Premium Billing Reconciliation

Reconcile one account, currency and gross-premium-receivable basis for a stated period. Preserve the opening prior-day close and reported period-end close. Debit movements increase receivable; receipts, credit adjustments and writeoffs decrease it. Refunds increase receivable. Never equate cash received with premium earned, premium written with billed receivable, or an overdue balance with a legal lapse.

Trace a reversal to a unique earlier in-period movement of the same policy/currency and exact amount. Partial reversals, opening-period reversals and reversing a reversal require a separately reviewed method. Duplicate, incompatible, unknown or out-of-period movements withhold the aggregate. A known control difference remains a reported break with reproducible arithmetic.

Keep invoice aging separate from account movement reconciliation. Aging needs an opening invoice inventory that equals the opening balance, new invoice IDs, due dates and allocations tied to live receipts/credits/writeoffs. Unapplied cash is not silently netted against an arbitrary invoice. This bounded aging method withholds aging for refund/debit-adjustment allocation complexity; the account-level bridge can remain available. No collection or cancellation instruction is produced.

## Native preparation and review

Read [references/source-map.md](references/source-map.md) for the structured input and [references/domain-rules.md](references/domain-rules.md) for method limits. Preserve supplied unknowns, conflicting versions and source passages. Do not manufacture missing facts to satisfy the schema. The examples are invented records, not institutional rule profiles.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Validate the saved output with `python scripts/validate_output.py OUTPUT.json`; this recomputes the native result from retained evidence. Use [assets/output-template.md](assets/output-template.md) to present a readable professional draft. Keep authored interpretation separate from the deterministic artifact and cite the underlying source passages.

Follow [references/controls.md](references/controls.md) and [references/handoffs.md](references/handoffs.md). [references/insurance-contract.md](references/insurance-contract.md) describes shared provenance and status fields. The receiving workflow must validate its actual native input. A role label, hash, complete checklist or prior approval is not permission to act.

Run `python scripts/test_domain.py` and the checks in [evals/evals.json](evals/evals.json). Local checks do not establish specialist or deployment acceptance.

See [native workflow foundation](references/insurance-foundation.md) for source-bound context mappings, inherited uncertainty and output validation.
