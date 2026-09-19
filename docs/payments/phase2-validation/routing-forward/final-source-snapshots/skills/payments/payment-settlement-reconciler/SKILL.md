---
name: payment-settlement-reconciler
description: >-
  Explain merchant payout reports in report-only explain-payout mode, or reconcile settlement files, effective fees/reserves, bank cash and ledger evidence in reconcile-settlement mode. Surface mismatches and incomplete evidence without generating accounting entries or executing repairs.
license: MIT
compatibility: Python 3.10+ for bundled offline checks; authenticated read-only source connectors are deployment responsibilities.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Settlement operations / finance operations"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Settlement Reconciler

Explain merchant payout reports or reconcile settlement files to bank cash and ledger
evidence. Select the mode explicitly. Preserve source discrepancies, incomplete evidence
and duplicate ambiguity; issue investigation handoffs without accounting instructions.

## Modes and routing

- **explain-payout**: informational report-only mode. Normalize signed report lines, show
  gross-to-net components, neutral fee metrics, declared funding comparisons and data
  gaps. Bank and ledger files are not prerequisites. A funding mismatch is a valid result
  to surface; it must not fail output validation or be hidden. This incorporates the former
  settlement report summarizer.
- **reconcile-settlement**: compare scoped network gross, processor waterfall and net,
  bank cash, ledger net and effective fee/reserve schedule. Report each check independently.
  Unsupported checks remain not evaluable.

Individual transaction matching belongs to payment-transaction-reconciler. Use
bank-payment-exception-investigator for chronology and cause investigation, merchant-payment-cost-analyzer
for pricing advice, iso-20022-message-interpreter for message interpretation, and
gl-reconciler for accounting analysis requiring a chart of accounts and booking policy.
This skill never generates balancing journals from unexplained differences.

## Workflow

1. Select the mode and establish legal entity, account, currency, settlement cycle,
   as-of date and versioned configuration. Read the relevant
   [domain rules](references/domain-rules.md); payout mode is detailed in
   [payout explanation](references/payout-explanation.md).
2. Retrieve masked source evidence read-only. Missing source files and fields remain
   unknown. Match only within all four partition dimensions plus match_key.
3. Run python3 -B `scripts/validate_input.py` INPUT.json, then
   python3 -B `scripts/calculate_or_transform.py` INPUT.json.
4. Review all checks, source lines and partial subtotals. Quarantine duplicate groups
   instead of selecting a first record or summing ambiguous entries. Never net across
   currencies, entities, accounts or cycles.
5. Run python3 -B `scripts/validate_output.py` OUTPUT.json --input INPUT.json.
   The validator recomputes the complete result. A discrepant payout is valid if the
   discrepancy and source figures are accurately represented.
6. Explain the result or route an investigation via [handoffs](references/handoffs.md).
   External delivery requires the reviewer's authorization.

## Outputs and boundaries

Both modes retain an input snapshot and content hash for reproducibility; these do not
prove authentication. Evidence defaults to supplied. Settlement mode emits partitioned
source values and totals, per-check signed differences, pending items and read-only
investigation handoffs. It does not sum overlapping gross/fee/cash/ledger break amounts
into a misleading total loss. Payout mode emits categories, observed subtotals,
calculated/reported/funding figures, neutral fee metrics, checks and evidence gaps.

fully_evaluated_and_matched describes only the supplied evidence and configured checks.
No output is an approval, journal, payment repair, confirmation of bank receipt, or
system-of-record closure. Payout explanation always leaves bank-cash confirmation and
ledger reconciliation false.

## Missing evidence and timing

A missing amount is not zero. No schedule/rate/precision means the affected fee or reserve
check is not evaluable. Schedule matching includes legal entity, account, currency,
scheme and effective date; overlapping schedules are ambiguous.

Classify a missing bank receipt as pending only when an explicit, cited funding due date
is later than as_of. Do not derive a universal calendar-day lag from period end.
A reached/unknown/conflicting due date remains an unresolved missing-bank issue.
The code does not compute business calendars, contractual due dates or rail deadlines.

## Verification

Use [controls](references/controls.md) and [source map](references/source-map.md).
Run python3 -B `scripts/regression_tests.py`; `evals/evals.json` contains commands and
workflow scenarios. Domain-owner acceptance and model evaluation are separate from the
deterministic script checks.
