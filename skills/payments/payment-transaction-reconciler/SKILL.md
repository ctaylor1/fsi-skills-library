---
name: payment-transaction-reconciler
description: >-
  Reconcile individual payment references across gateway, processor, bank and ledger evidence; surface scoped mismatches, missing values and duplicate ambiguity, and draft read-only investigation handoffs. Use for transaction-level matching, not settlement-file reconciliation or journal posting.
license: MIT
compatibility: Python 3.10+ for bundled offline checks; authenticated read-only source connectors are deployment responsibilities.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Merchant / reconciliation analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Transaction Reconciler

Reconcile individual payment references across gateway, processor/acquirer, merchant,
bank and ledger evidence. Produce cited source comparisons, explicit gaps, quarantined
ambiguous groups, and investigation handoffs. An equal bank/ledger pair does not erase
a gateway or processor discrepancy. This is read-only analysis.

## Use and boundaries

Use for transaction/order matching, missing records, duplicate references, amount
differences, and explicitly normalized lifecycle-state differences. Batch/payout/settlement
records always go to payment-settlement-reconciler, including equal records. GL account
balance certification belongs to gl-reconciler; exception chronology belongs to
bank-payment-exception-investigator. Do not infer correcting entries, reverse unmatched ledger
items, post journals, move money, or mark a system-of-record case closed.

## Workflow

1. Confirm the as-of date, versioned tolerance and expected source set. Read
   [domain rules](references/domain-rules.md) for the input and arithmetic contract.
2. Retrieve masked records read-only. Every row needs a legal entity, account, currency,
   settlement cycle, transaction reference, source, dated citation and record ID.
   Match within that complete partition only.
3. Run python3 -B `scripts/validate_input.py` INPUT.json, then
   python3 -B `scripts/calculate_or_transform.py` INPUT.json.
4. Inspect all comparisons and evidence. Duplicate/ambiguous groups are quarantined;
   their amounts cannot contribute to usable totals. Missing records or amounts remain
   unknown. Only bank evidence supports cash received.
5. Validate with python3 -B `scripts/validate_output.py` OUTPUT.json --input INPUT.json.
   This recomputes every output field and binds the supplied input. A matching hash does
   not authenticate external evidence.
6. Explain the observed differences and route unresolved evidence through the
   [handoff contract](references/handoffs.md). A route requests analysis; it grants no authority.

## Inputs and output

The executable schema and examples are in [domain rules](references/domain-rules.md) and
`evals/files/ledger_example.json`. Money should be JSON decimal strings. Boolean and
nonfinite amounts fail validation; null/absent amounts become evidence gaps.

The output contains source_snapshot, input_hash, groups, partition_totals,
routed_groups, investigation_handoffs, coverage counts, warnings and a read-only
disclaimer. Evidence remains supplied; arithmetic does not upgrade it to authenticated
or sufficient. There is no global monetary total across partitions and no hypothetical
post-adjustment tie-out. fully_evaluated_and_matched is a report result, never a posted
or approved case disposition.

## Controls and failure handling

Use [controls](references/controls.md) and [source map](references/source-map.md).
An incomplete source cannot yield a zero-based balance. Comparisons outside tolerance
remain visible even if their signed differences offset. Report retrieval failures and stale
or conflicting source dates; do not fabricate missing records. External delivery requires
the reviewer's authorization. All bundled operations are local and read-only.

Run python3 -B `scripts/regression_tests.py` for partition, duplicate, precision, missing-data,
upstream-discrepancy, routing and output-binding regressions. Deterministic evaluations are
in `evals/evals.json`; model workflow evaluation and domain-owner acceptance remain separate.
