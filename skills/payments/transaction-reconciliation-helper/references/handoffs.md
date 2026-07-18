# Adjacent-Skill Handoffs — transaction-reconciliation-helper

This skill produces a cited **transaction-level reconciliation** (`recon_id`): matched
records, classified breaks with lineage, tie-out totals, and **proposed** resolution
entries. It then stops. It does not post entries, close breaks, or reconcile settlement
files.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `settlement-break-reconciler` | The break is a **settlement-file / cash-ledger** break — acquirer/processor settlement file vs bank cash, fees, or reserves | `recon_id` + routed break rows + amounts |
| `payment-exception-investigator` | A break traces to a **payment exception / ISO 20022 case** (rejected/returned/held payment, camt/pacs status) | `recon_id` + the affected `txn_ref`(s) |
| `iso-20022-message-interpreter` | The mismatch is a **message-parsing / field** question (pain/pacs/camt) rather than a record match | the message + affected fields |
| `chargeback-dispute-packager` | An amount/status mismatch is actually a **merchant chargeback/refund** to package | focal txn + evidence |
| `settlement-report-summarizer` | The user wants a **settlement report summary**, not a transaction-level match | report + period |

## Upstream (may call this skill)

`payment-failure-diagnoser` and merchant-operations skills may request a transaction-level
reconciliation for a period. A scheduled monitor is **not** used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill matches records, classifies breaks, and **proposes** entries only; it must not
  post, close a break, or resolve settlement-file breaks — those belong to the human, the
  ledger system, and `settlement-break-reconciler`.
- Routed settlement breaks are handed off **without** a proposed ledger entry, so the
  settlement workflow is the single owner of those corrections (no double-posting).
- Downstream skills reuse the `recon_id` lineage rather than re-matching the records.
