# Adjacent-Skill Handoffs — settlement-break-reconciler

This skill produces a cited **settlement break pack** (`reconciliation_id`) with classified
breaks, quantified impact, tie-out totals, and **proposed-only** corrections — then stops. It
does not post, execute, investigate to disposition, or close.

## Sibling boundary (do not duplicate)

- **`transaction-reconciliation-helper`** reconciles **transaction-level** processor,
  gateway, bank, ledger, and merchant records. It explicitly routes settlement-file and
  cash-ledger breaks to *this* skill. Conversely, if the request is per-transaction (not
  file/period cash tie-out), route to `transaction-reconciliation-helper`.
- **`gl-reconciler`** reconciles **general-ledger balances** to subledgers/source systems. If
  the anchor is a GL balance rather than a settlement file, route there.

## Upstream (may call this skill)

| Upstream skill | Hands off | This skill consumes |
| -------------- | --------- | ------------------- |
| `settlement-report-summarizer` | A plain-language settlement report the user then wants reconciled | settlement/period + source files |
| `payment-failure-diagnoser` | A cash/settlement shortfall traced to the settlement leg | period + affected batches |

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-exception-investigator` | A break needs a structured chronology / party-and-status investigation (e.g. ISO 20022 camt exceptions) | `reconciliation_id` + break_id |
| `payment-repair-assistant` | An approved break requires an actual repair/resubmission of a held or rejected payment (R4, approval-gated) | approved break + evidence |
| `gl-reconciler` | The proposed correcting journals must be reconciled and staged on the GL side | proposed corrections + citations |
| `month-end-close-orchestrator` | The breaks and proposed corrections feed the close, where **all postings and sign-offs are gated** | `reconciliation_id` + corrections |

Posting a proposed correcting journal is **not** performed by any of these as an autonomous
act — `payment-repair-assistant` and `month-end-close-orchestrator` gate on human approval
before any write. If no catalog skill fits (e.g. a network chargeback dispute or a contract
fee-rate renegotiation), route to the appropriate **operations / finance / licensed
specialist** in prose rather than inventing a skill.

## Duplicate-execution prevention

- This skill computes **breaks and proposed corrections only**; it never posts, closes, or
  investigates to disposition.
- The deterministic `reconciliation_id` + `correction_id`s make re-runs idempotent, so
  downstream skills reuse the identified breaks rather than re-deriving them.
