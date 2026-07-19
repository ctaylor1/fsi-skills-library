# Adjacent-Skill Handoffs — payment-exception-investigator

Investigation (this skill) sits between **diagnosis/interpretation** upstream and **repair
execution / specialist adjudication** downstream. Each is a separate control activity with
distinct entitlements, evidence depth, and case states. This skill emits a durable `case_id` +
evidence bundle and must not perform the upstream triage or the downstream money movement.

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `payment-failure-diagnoser` | First-line, single-payment diagnosis; escalates multi-message / disputed / recall cases here for full investigation. |
| `iso-20022-message-interpreter` | Decodes raw pacs/camt XML into the structured message fields this skill consumes (a utility, not a decision). |

## Downstream (this skill routes / hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-repair-assistant` | An approved repair / return / resubmission (money movement) is to be executed | `case_id` + recommendation + corrected fields |
| `sanctions-match-adjudicator` | Regulatory reason (RR04) or a sanctions hold on the payment | `case_id` + flag evidence (no adjudication here) |
| `payment-fraud-case-investigator` | A fraud indicator on the exception | `case_id` + evidence bundle |
| `dispute-operations-assistant` | The exception is really a customer dispute rather than a message exception | `case_id` + parties + amounts |
| `chargeback-dispute-packager` | A card-network chargeback needs packaging | `case_id` + transaction evidence |
| `transaction-reconciliation-helper` / `settlement-break-reconciler` | The exception is a reconciliation / settlement break, not a message reject/return | `case_id` + amounts + references |

## Human / operations handoffs (no catalog skill)

- **Payments approver / operations** — adjudicates every recommendation and authorizes the
  camt.029 recall response, return, or repair. This is a human gate, not a skill.
- **Correspondent bank contact** — an information request to the counterparty agent is drafted
  here and *sent by a human* after approval.

## Duplicate-execution prevention

- This skill **does not** diagnose (upstream), interpret raw XML (upstream utility), execute
  repairs/returns, or adjudicate sanctions/fraud (downstream). It builds the evidence bundle and
  a recommendation once.
- A `possible-duplicate` link points to the open `case_id`; a human confirms — never auto-merged.
- Downstream consumers use the emitted `case_id`/bundle rather than re-investigating.
