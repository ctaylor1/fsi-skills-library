# Adjacent-Skill Handoffs — corporate-action-election-assistant

This skill owns the **plan → validate → approve → submit → verify → audit** lifecycle for a
**voluntary** corporate-action election. It does not interpret notices, decide which option
is better, compute tax, monitor settlement, or resolve trade breaks.

## Upstream (hands a confirmed election request here)

| Upstream source | Handoff artifact |
| --------------- | ---------------- |
| `corporate-action-interpreter` (interprets the notice, options, dates, entitlements) | `interpretation_id`, `event_id`, event_type, options, deadlines, per-option entitlement |
| `portfolio-holdings-summarizer` (normalizes the eligible position) | eligible record-date `position` + as-of |

The holder (or an authorized instruction on the account) selects the option; this skill
validates eligibility, deadline, option, and quantity, and stages the election for approval.

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `post-trade-settlement-monitor` | The elected proceeds/positions are settling or failing after submission |
| `transaction-reporting-quality-checker` | The resulting transaction needs regulatory-reporting completeness/quality review |
| `trade-break-resolver` | The matter is a trade/position break across systems, not a CA election |
| `corporate-action-interpreter` | The user still needs the notice explained (terms, options, deadline) — no election intent yet |
| Licensed representative / registered advisor | The user asks **which option to elect** (investment advice) — never answered here |
| Licensed tax professional | The user asks for a personalized tax result or cost-basis treatment |
| Corporate-actions operations / custodian-agent desk | Off-catalog, over-limit, past-cutoff, irreversible, or a late/protect instruction |

## Duplicate-execution prevention

- Only this skill submits the election; upstream interpretation skills never instruct the
  custodian/agent.
- Submission is keyed by `plan_id` + step idempotency keys — re-invocation never double-submits.
- If an election for the same event/account already exists, the precondition check surfaces
  it and this skill halts (amend/supersede, never a second parallel election).
