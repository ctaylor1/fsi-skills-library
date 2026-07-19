# Adjacent-Skill Handoffs — operational-risk-event-analyzer

This skill produces a cited operational-risk **analysis pack** (`analysis_id`) and stops. It
does not decide, escalate, file, close, or write a system of record — those are human /
authorized-system actions performed with the pack as input.

## Downstream (route the human/adjudicator to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `third-party-risk-assessor` | The root cause is a third party/vendor and its controls need assessment | `analysis_id` + cause evidence |
| `cyber-incident-response-coordinator` | The event is a live/material cyber incident needing coordinated response | `analysis_id` + incident refs |
| `ai-incident-investigator` | The event is an AI/model failure needing model-governance investigation | `analysis_id` + model refs |
| `suspicious-activity-report-drafter` | A financial-crime dimension makes a SAR narrative appropriate (draft-only, human-filed) | `analysis_id` + evidence |
| `complaint-resolution-assistant` | Customers were harmed and complaints must be handled | `analysis_id` + affected-customer context |
| `key-risk-indicator-monitor` | The event should feed or re-threshold a KRI trend | `analysis_id` + severity/impact |
| `risk-control-self-assessment-assistant` | The control theme should refresh an RCSA control rating | `analysis_id` + control themes |
| `operational-resilience-reporter` | A resilience/service-disruption event needs resilience reporting | `analysis_id` + impact |

## Upstream (may call this skill)

`key-risk-indicator-monitor` breaches, `real-time-payment-risk-monitor` alerts, and
control-self-assessment work may surface an event that needs this analysis. A scheduled monitor
is **not** used here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill **analyzes and recommends only**; it must not reach an escalation decision, file,
  close the event, or update the register — those belong to the human adjudicator and the
  downstream skills.
- Downstream skills reuse the `analysis_id` and its cited evidence rather than re-classifying or
  re-quantifying the event.
- Only real catalog skills are referenced above; where no catalog skill fits (e.g., the ERM
  adjudication decision itself, board escalation, or a regulatory filing), the handoff is to a
  **human adjudicator / authorized system**, not another skill.
