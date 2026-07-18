# Adjacent-Skill Handoffs — settlement-report-summarizer

This skill produces a **normalized settlement snapshot** and stops. It does not reconcile,
investigate, optimize, advise, or act. Downstream skills consume the snapshot via its
durable `snapshot_id`.

## Downstream (this skill hands off to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `settlement-break-reconciler` | Merchant wants the settlement matched to their own records / expected amounts, or asks "why is my deposit different from my sales/ledger" | `snapshot_id` + normalized category table |
| `transaction-reconciliation-helper` | Reconciliation at the individual transaction/order level (not the settlement roll-up) | `snapshot_id` + period |
| `payment-exception-investigator` | A specific break, missing funding, held reserve, or exception needs investigation and a disposition | `snapshot_id` + exception reference |
| `payment-failure-diagnoser` | Merchant asks why specific payments failed or did not settle | account/period context |
| `iso-20022-message-interpreter` | Merchant wants a specific `camt.053/054`/`pacs` message or field decoded | the raw message |
| `merchant-fee-optimizer` | Merchant asks whether fees are competitive, or how to reduce them / change pricing | `snapshot_id` + fee breakdown |
| `chargeback-dispute-packager` | Merchant wants to contest a chargeback shown on the settlement | chargeback reference |

## Upstream (may call this skill)

`settlement-break-reconciler`, `merchant-fee-optimizer`, and `payment-exception-investigator`
may request a fresh settlement snapshot from this skill rather than re-normalizing the
processor report themselves.

## Duplicate-execution prevention

- This skill **only summarizes**; it must not perform reconciliation, break classification,
  exception investigation, fee optimization, or dispute work — those belong to the skills above.
- Downstream skills must **not** re-normalize a settlement report when a valid `snapshot_id`
  for the same `report_id` + as-of already exists; they reuse it.
