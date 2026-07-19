# Adjacent-Skill Handoffs — real-time-payment-risk-monitor

This skill is a **scheduled, read-only, alert-only** monitor. It produces a cited alert pack
(`run_id`) with per-alert `fingerprint`s and stops. It does **not** investigate to
disposition, adjudicate a sanctions match, model liquidity scenarios, decide, file, act on a
payment or account, or close an alert or case. Those are human payments-risk / fraud / AML
actions, supported by the downstream skills below.

## Downstream (route the human reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-fraud-case-investigator` | A flagged account needs a full fraud investigation (device, identity, behavior, beneficiary, network) and a disposition recommendation | `run_id` + account + alert evidence |
| `aml-alert-triager` | A mule / laundering pattern needs first-line AML triage with customer, entity, and network context | `run_id` + account + pattern evidence |
| `transaction-monitoring-alert-investigator` | An AML alert escalated from triage needs substantive investigation | account + prior-case scope |
| `sanctions-match-adjudicator` | A watchlist / sanctions candidate hit needs true-match adjudication | payment(s) + counterparty + list |
| `liquidity-risk-scenario-analyzer` | A settlement-liquidity alert needs stress / scenario modeling of prefunded positions | `position_id` + utilization evidence |
| `payment-exception-investigator` | The flag is really an ISO 20022 exception (pacs reject, camt) needing a chronology | message / payment ids |
| `payment-failure-diagnoser` | The concern is a failed or delayed payment rather than a risk pattern | payment ids + status |
| `iso-20022-message-interpreter` | A raw pain/pacs/camt message must be parsed and validated before triage | message payload |
| `payment-repair-assistant` | After human review, an approved exception/investigation case needs a validated, authorized repair plan | approved case id |

Disposition itself — investigating to a finding, adjudicating a match, deciding an
account/payment action, filing a SAR, or closing the case — is performed by the **payments-risk
/ fraud / AML analyst and their entitled systems**, never by this monitor.

## Upstream (what invokes this skill)

This is a **scheduled monitor** (`aws-fsi-scheduled-agent: read-only-monitoring`): it is
triggered by its schedule (or an ad-hoc reviewer run), not by another skill. A payments-risk or
fraud-operations analyst may also run it on demand against a specific window or account.

## Duplicate-execution prevention

- The monitor computes and evidences **alerts only**; it must not reach a disposition, contact
  a customer, take/recommend a payment or account action, or file/close anything — those belong
  to the human reviewer and the downstream skills.
- Cross-run **deduplication** (fingerprint vs `open_alerts`) prevents the same persistent
  pattern from being re-raised every scheduled run; still-open items remain visible as open
  rather than being silently cleared.
- Downstream skills consume the `run_id` / alert evidence rather than re-deriving thresholds or
  re-screening the whole flow.
