# Adjacent-Skill Handoffs — market-surveillance-alert-investigator

Triage, investigation, and adjudication are **separate control activities** with different
entitlements, evidence depth, and case states. This skill is the **investigation** step: it
consumes a triage escalation, builds a durable, cited evidence bundle, and hands a
disposition **recommendation** to an authorized human adjudicator. It never closes,
determines, or files.

## Upstream (feeds this skill)

| Upstream skill | Handoff artifact consumed |
| -------------- | ------------------------- |
| `surveillance-alert-triager` | Escalated alert with `triage_case_id`, `escalated_by`, prioritized context. Investigation **requires** this provenance; an un-triaged alert is routed back to triage, not investigated. |

## Downstream / lateral (this skill routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `communications-compliance-reviewer` | Electronic-comms alert needs a full supervision / disclosure / retention review beyond the surveillance indicators | `case_id` + flagged messages + chronology |
| `adverse-media-investigator` | Insider/MNPI signal references an external event/entity to corroborate | `case_id` + entity + event reference |
| `best-execution-reviewer` | The concern is really execution quality / routing / venue, not manipulation | `case_id` + order/trade/routing evidence |
| `conflicts-of-interest-reviewer` | A personal-account / desk conflict is implicated by the activity | `case_id` + parties + incentive evidence |
| `sanctions-match-adjudicator` | A counterparty/entity raises a sanctions potential-match question | `case_id` + entity identifiers |

## Adjudication (human, not a skill)

The substantive **disposition** — closing the case, making (or declining) a market-abuse
determination, and any **STOR/SAR or regulator filing** — is performed by a qualified
supervisor / compliance officer / MLRO through the approval broker and the firm's regulatory
reporting process. There is deliberately **no skill** that performs these regulated actions;
this skill produces the recommendation and evidence they adjudicate.

## Duplicate-execution prevention

- This skill does **not** triage (that is `surveillance-alert-triager`) and does **not**
  adjudicate/close/file (that is a licensed human).
- A durable, idempotent `case_id` (`MKT-SURV-<alert_id>`) lets the adjudicator and any
  re-run reference the same case rather than forking a new one.
- An overlap with an open case is emitted as `possible-duplicate` (linked) for human
  confirmation — never auto-merged and never re-investigated in parallel.
