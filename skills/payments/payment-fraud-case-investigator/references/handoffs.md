# Adjacent-Skill Handoffs — payment-fraud-case-investigator

Triage/monitoring, **investigation** (this skill), specialist adjudication, and downstream
action are **separate control activities** with different entitlements, evidence depth, and
case states. This skill consumes a triaged alert, builds a durable-`case_id` evidence bundle,
and emits a disposition **recommendation** — it never adjudicates, closes, blocks, or files.

## Upstream (feeds this skill)

| Upstream skill | Produces | This skill consumes |
| -------------- | -------- | ------------------- |
| `real-time-payment-risk-monitor` | Read-only scheduled fraud alerts / queue items | The alert to investigate |
| `payment-failure-diagnoser` | Payment declines/exceptions surfacing suspected fraud | The referred case |
| `account-anomaly-screener` | Banking anomaly review flagging suspected fraud | The referred case |

Triage/monitoring **populates**; it does not investigate. This skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Downstream / lateral (this skill routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `sanctions-match-adjudicator` | Sanctions/adverse-media proximity flag present | `case_id` + flag evidence |
| `phishing-and-bec-investigator` | APP scam / BEC social-engineering indicators | `case_id` + bundle |
| `suspicious-activity-report-drafter` | **Only after a human adjudicator** concludes a SAR may be warranted (never from this skill directly) | adjudicated case |
| `payment-repair-assistant` | Adjudicated case needs the payment repaired/returned operationally | `case_id` + adjudication |
| `chargeback-dispute-packager` | The matter is a card dispute/chargeback rather than fraud | `case_id` + transaction evidence |
| `dispute-operations-assistant` | Dispute-lifecycle handling of a related cardholder dispute | `case_id` + context |
| `transaction-monitoring-alert-investigator` | Money-laundering typology is the primary concern | `case_id` + bundle |
| `adverse-media-investigator` | Adverse-media enrichment on a party is needed | party ref + trigger |

## Non-skill (human / operations) handoffs

- **Fraud adjudicator / case approver** — makes the fraud determination, closes the case,
  and authorizes any block, recovery, or customer commitment. This skill supplies evidence
  and a recommendation only.
- **Fraud operations** — executes an authorized block/return after adjudication.
- **FIU / BSA officer** — owns the SAR decision and filing (human-performed).

## Duplicate-execution prevention

- This skill **does not** monitor/triage, adjudicate sanctions or BEC, draft/file SARs, or
  execute payment repair — those belong up- or downstream.
- The adjudicator and downstream skills consume this skill's `case_id`/bundle rather than
  re-investigating.
- A `route-specialist` disposition hands the case over with its `case_id`; the specialist
  does not re-open a parallel investigation.
