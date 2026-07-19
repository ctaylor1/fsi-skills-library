# Adjacent-Skill Handoffs — advisor-follow-up-assistant

Drafting the follow-up package (this skill), reviewing a recommendation's suitability, building an
IPS, and trading are **separate control activities** with different entitlements, evidence, and
approvals. This skill emits a durable `followup_id` + draft package; it must not perform the review,
send the communication, write the CRM, or trade.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `client-review-preparer` | The review brief / meeting context that the follow-up summarizes | Review brief + meeting record |
| `financial-goal-progress-analyzer` | Goal shortfalls / levers discussed in the meeting that inform action items | Documented objectives + gaps |
| `retirement-income-scenario-modeler` | Income/withdrawal ranges discussed that inform distribution action items | Modeled ranges (not guarantees) |

The meeting record itself (CRM / notes) is the raw input. This skill is **interactive**
(`aws-fsi-scheduled-agent: no`); it never runs unattended.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `suitability-reg-bi-reviewer` | Any recommendation discussed in the meeting needs a suitability / Reg BI and supervision review (never approved here) | `followup_id` + recommendation ref + source map |
| `investment-policy-statement-builder` | The follow-up calls for building or refreshing the IPS | `followup_id` + documented change triggers |
| `portfolio-rebalancing-assistant` | An action item is to move a portfolio toward its targets (R4, advisor + client authorization) | `followup_id` + drift evidence + target bands |
| `portfolio-proposal-comparator` | The client wants competing proposals weighed | `followup_id` + constraints |
| `senior-investor-protection-screener` | Senior-investor, diminished-capacity, or trusted-contact concerns surface in the meeting | `followup_id` + flagged concern evidence |

## Non-catalog / human & operations handoffs

- **Advisor** owns the recommendation and the content; a **supervisory principal / compliance**
  owns communication and supervision sign-off (FINRA Rule 2210 principal approval of retail
  communications, Rule 3110 supervision). These are human roles captured in the draft's approval
  block as `pending` — no catalog skill grants them.
- **Sending the communication, writing the CRM, scheduling the next meeting, and archiving to
  books-and-records** are operations-team / advisor steps performed out-of-band **after** human
  approval; this skill never initiates them.

## Duplicate-execution prevention

- This skill **does not** review suitability, build the IPS, trade, send, or write the CRM — those
  belong downstream or to humans/operations.
- The suitability reviewer consumes the `followup_id` / recommendation ref rather than re-drafting
  the package.
- A re-run supersedes the prior draft under the same `followup_id` and records what changed; it does
  not spawn a parallel, conflicting follow-up.
