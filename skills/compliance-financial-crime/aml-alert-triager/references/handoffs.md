# Adjacent-Skill Handoffs — aml-alert-triager

Triage (this skill) and investigation are **separate control activities** with different
entitlements, evidence depth, throughput metrics, and case states.

## Downstream (this skill escalates to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `transaction-monitoring-alert-investigator` | Any non-suppressed alert needing substantive investigation | `case_id` + escalation bundle + recommended priority |
| `sanctions-match-adjudicator` | Sanctions/adverse-media proximity flag present | `case_id` + flag evidence |
| `suspicious-activity-report-drafter` | Only after investigation concludes a SAR may be warranted (never from triage) | investigator's approved case |
| `customer-risk-rating-reviewer` | Triage surfaces a rating/trigger question | customer_id + trigger evidence |

## Upstream (feeds this skill)

The transaction-monitoring system produces the raw alert queue. This skill is **interactive**
triage (`aws-fsi-scheduled-agent: no`); a read-only monitor may *populate* a queue but must
not triage or act.

## Duplicate-execution prevention

- This skill **does not** perform investigation, typology conclusions, sanctions
  adjudication, or SAR drafting — those belong downstream.
- The investigator consumes the triage `case_id`/bundle rather than re-triaging.
- A `possible-duplicate` link is resolved by a human, not auto-merged here.
