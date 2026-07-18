# Domain Rules — chargeback-dispute-packager

Merchant-side representment logic applied by
[../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). All values are
a **versioned contract** (`ruleset_version`); the defaults below are illustrative and must
be confirmed against the current card-network rules at deployment. This reference does not
adjudicate disputes and does not guarantee outcomes.

## Reason-code catalog (default)

| Code | Title | Network | Window (days) | Category | Required-evidence groups (AND across groups; OR within a group) |
| ---- | ----- | ------- | ------------- | -------- | --------------------------------------------------------------- |
| VISA-10.4 | Fraud – Card-Absent Environment | VISA | 30 | fraud | (avs_result \| cvv_result \| three_ds_authentication); (proof_of_delivery \| proof_of_service); prior_transaction_history |
| VISA-13.1 | Merchandise/Services Not Received | VISA | 30 | consumer_dispute | (proof_of_delivery \| proof_of_service); order_confirmation; terms_of_service |
| VISA-13.3 | Not as Described or Defective | VISA | 30 | consumer_dispute | item_description_evidence; terms_of_service; proof_no_valid_return |
| VISA-12.6 | Duplicate Processing / Paid by Other Means | VISA | 30 | processing_error | (distinct_transaction_proof \| refund_proof) |
| MC-4853 | Cardholder Dispute | MASTERCARD | 45 | consumer_dispute | (proof_of_delivery \| proof_of_service); order_confirmation; terms_of_service |
| MC-4837 | No Cardholder Authorization | MASTERCARD | 45 | fraud | (avs_result \| cvv_result \| three_ds_authentication); (proof_of_delivery \| proof_of_service); prior_transaction_history |

An unknown reason code yields `needs-data` (map it to the catalog first); it is never
packaged on a guess.

## Deterministic computations

1. **Representment deadline.** `representment_due_date = chargeback_date + window_days`;
   `days_remaining = due − as_of_date`. `deadline_status = on_time` if `days_remaining ≥ 0`
   else `past_due`. A `past_due` dispute is flagged `past-deadline` and never packaged.
2. **Evidence completeness.** For each required group, at least one listed evidence `type`
   must be present. Any unsatisfied group → `missing_groups` → `insufficient-evidence`.
3. **Transaction identity tie-out.** The disputed transaction currency must equal the
   dispute currency and `dispute_amount ≤ transaction.amount` (partial disputes allowed).
   Every exhibit carrying a `txn_id`/`arn` must reference the disputed transaction; any
   foreign reference → `identity-mismatch`.
4. **Compelling-evidence eligibility** (fraud categories only). Flagged `eligible` when ≥ 2
   prior undisputed transactions sharing cardholder identifiers are supplied (e.g., Visa
   CE3.0 pattern). This is an **eligibility flag for human use**, not an outcome prediction.
5. **Narrative fidelity.** Every narrative point must cite an `exhibit_id` present in the
   bundle. An unsupported point → `unsupported-claim`; the package is not assembled.

## Status precedence

`needs-data` (unknown code) → `past-deadline` → `insufficient-evidence` →
`identity-mismatch` → `unsupported-claim` → `draft-representment`. Only
`draft-representment` is `packageable`.

## What the rules never do

- No fraud/liability determination and no "who wins" prediction.
- No submission — the package is drafted for authorized human review and filing.
- No fabrication — missing evidence is reported, never invented.
