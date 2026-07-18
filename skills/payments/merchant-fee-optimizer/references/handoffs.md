# Adjacent-Skill Handoffs — merchant-fee-optimizer

This skill produces a cited **fee-optimization pack** (`analysis_id`) with estimated,
assumption-backed savings opportunities and then stops. It does not negotiate, sign,
terminate, switch, reconcile, or dispute.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `settlement-break-reconciler` | The question is settlement/funding vs. ledger reconciliation and break classification, not pricing | statement/settlement file + period |
| `transaction-reconciliation-helper` | Transaction-level reconciliation of processor detail against records | transaction detail + period |
| `settlement-report-summarizer` | The user wants a plain summary of a settlement report, not a savings analysis | settlement report |
| `chargeback-dispute-packager` | A specific transaction needs a chargeback/dispute package | focal txn + evidence |
| `network-rules-change-tracker` | The driver is a card-network rule/interchange schedule change | scheme + effective date |
| `iso-20022-message-interpreter` | The input is an ISO 20022 message needing field-level interpretation | message |

## Upstream (may call this skill)

A merchant/payments finance analyst invokes this skill interactively with a processing
statement. It is **not** a scheduled agent (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill **estimates and evidences opportunities only**; it must not reconcile
  settlement breaks, dispute transactions, interpret ISO 20022 messages, or take/recommend a
  binding contract or processor action — those belong to the human and the downstream skills.
- Downstream skills reuse the `analysis_id` evidence rather than recomputing fee estimates.
- If asked to negotiate, sign, terminate, or switch, stop and hand the decision back to the
  human — no skill in this library performs that action autonomously.
