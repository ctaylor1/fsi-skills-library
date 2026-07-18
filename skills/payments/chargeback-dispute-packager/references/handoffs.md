# Adjacent-Skill Handoffs — chargeback-dispute-packager

This skill is **merchant-side** representment drafting. It packages evidence for a human to
review and submit; it does not adjudicate disputes, reconcile settlement, or investigate
fraud. Those are separate control activities with distinct entitlements.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| `network-rules-change-tracker` | Current reason codes, required evidence, and representment deadlines (versioned) | `ruleset_version` + reason-code catalog |
| Acquirer / gateway records | The chargeback record and disputed transaction | `dispute_id`, ARN/auth code, chargeback date |
| Merchant OMS / fulfillment | Order, delivery, terms, and refund evidence | evidence exhibits with `exhibit_id` |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Issuer- or acquirer-**side** dispute handling / applying network rules from the bank's side | `dispute-operations-assistant` |
| Determining whether the transaction was **fraud** / investigating a fraud alert | `payment-fraud-case-investigator` |
| Reconciling transaction or settlement records / chargeback debits to the ledger | `transaction-reconciliation-helper`, `settlement-break-reconciler` |
| Understanding interchange/fee or downgrade economics of chargebacks | `merchant-fee-optimizer` |
| Tracking or interpreting a network **rule change** itself | `network-rules-change-tracker` |

## Downstream (human, not a skill)

The reviewed and approved package is submitted by an **authorized human** through the case
portal / acquirer interface. This skill emits a `dispute_id`-keyed draft package plus a
`reviewer_signoff_required` flag; it must not perform the submission.

## Duplicate-execution prevention

- This skill **does not** submit, reconcile, or adjudicate — those belong to the routes
  above or to a human.
- A package carries the `dispute_id` and `ruleset_version` so a reviewer works one authored
  draft rather than re-packaging.
- A `past-deadline`, `insufficient-evidence`, `identity-mismatch`, or `unsupported-claim`
  record is resolved by a human (obtain evidence / confirm identity), never force-packaged.
