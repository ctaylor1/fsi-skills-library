# Adjacent-Skill Handoffs — surveillance-alert-triager

Triage (this skill) and investigation are **separate control activities** with different
entitlements, evidence depth, throughput metrics, and case states.

## Downstream (this skill escalates to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `market-surveillance-alert-investigator` | Any non-suppressed trade- or e-comms-surveillance alert needing substantive investigation and disposition | `case_id` + evidence bundle (chronology, parties, amounts, citations) + recommended priority |
| `communications-compliance-reviewer` | E-comms alert whose substantive question is disclosures, supervision, or retention | `case_id` + message evidence + flagged aspect |
| `best-execution-reviewer` | Alert reframes as an execution-quality / routing / venue question rather than abuse | `case_id` + order/venue evidence |
| `conflicts-of-interest-reviewer` | Triage surfaces a personal-account-dealing or cross-side conflict question | affected parties + trigger evidence |

## Non-catalog / human handoffs

- **Substantive disposition, case closure, or any regulatory filing (STR/SAR/regulator
  report)** are performed by the **surveillance investigator / compliance approver and the
  filing function under human adjudication** — never by this skill and not modeled as a
  separate catalog skill.
- **Legal / MNPI-handling questions** route to the firm's **legal / control-room team**.

## Upstream (feeds this skill)

The surveillance platform (trade + e-comms scenarios) produces the raw alert queue. This
skill is **interactive** triage (`aws-fsi-scheduled-agent: no`); a read-only monitor may
*populate* a queue but must not triage or act.

## Duplicate-execution prevention

- This skill **does not** perform investigation, scenario/typology conclusions, or filing —
  those belong downstream.
- The investigator consumes the triage `case_id`/bundle rather than re-triaging.
- A `possible-duplicate` link is resolved by a human, not auto-merged here.
