# Adjacent-Skill Handoffs — dispute-operations-assistant

This skill is **issuer- and acquirer-side** dispute case-work: it applies current network
rules from the bank's side, validates reason codes and deadlines, assembles evidence, and
**drafts** case responses for a human to adjudicate and submit. Adjudication, funds movement,
submission, fraud determination, and merchant-side representment are separate control
activities with distinct entitlements.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| `network-rules-change-tracker` | Current reason codes, required evidence, response windows (versioned) | `current_rule_version` + reason-code registry |
| Issuer/acquirer dispute case system | The dispute/case record and role/stage | `case_id`, role, network, dates |
| Transaction / authorization + evidence sources | Transaction identity and typed exhibits | auth record, exhibits with source refs |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| **Merchant-side** representment / compelling-evidence packaging | `chargeback-dispute-packager` |
| Determining whether a transaction was **fraud** / investigating a fraud alert | `payment-fraud-case-investigator` |
| Interpreting or tracking a network **rule change** itself | `network-rules-change-tracker` |
| An **ISO 20022** payment exception / investigation (camt), not a card dispute | `payment-exception-investigator` |
| **Reconciling** chargeback debits or transactions to the ledger | `transaction-reconciliation-helper`, `settlement-break-reconciler` |
| Interchange/fee or downgrade **economics** of disputes | `merchant-fee-optimizer` |

## Downstream (human, not a skill)

The reviewed and approved case response is **adjudicated and submitted by an authorized
human** through the dispute case system. This skill emits a `case_id`-keyed draft package
plus `authorization_status: pending-human-authorization`; it must not decide, credit, submit,
file, or close.

## Duplicate-execution prevention

- This skill **does not** adjudicate, move funds, submit, or investigate fraud — those belong
  to the routes above or to an authorized human.
- Each record carries the `case_id` and `current_rule_version` so a reviewer works one
  authored draft rather than re-drafting.
- A `needs-data`, `evidence-insufficient`, `out-of-time-review`, or `rule-version-stale`
  record is resolved by a human (obtain data/evidence, confirm timing, refresh the rulebook),
  never force-drafted or auto-decided.
