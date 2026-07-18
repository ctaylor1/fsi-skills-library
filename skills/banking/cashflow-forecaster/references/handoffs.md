# Adjacent-Skill Handoffs — cashflow-forecaster

This skill produces a transparent, source-linked **cash-flow forecast** (`forecast_id`) with
base/upside/downside scenarios, drivers, and tie-outs, then stops. It does not advise, decide
eligibility, extend credit, or write a system of record.

## Downstream (route the human/user to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `financial-spreading-assistant` | The user needs standardized credit spreads / financial statements rather than a forward cash-flow view | history + statements |
| `retirement-income-scenario-modeler` | The question is long-horizon retirement income/drawdown, not near-term operating cash flow | goals + accounts |
| `financial-goal-progress-analyzer` | The user wants to measure progress toward stated budgets/goals using the forecast's cash flows | `forecast_id` |
| A licensed **advisor / lending workflow** (human) | The user asks "what should I do", or wants a loan/credit decision | `forecast_id` + drivers |

## Upstream (may call this skill)

`bank-statement-analyzer` or a relationship-manager copilot may request a forecast after
summarizing history. A scheduled agent is **not** used here (`aws-fsi-scheduled-agent: no`);
the skill is interactive.

## Boundary with advice and lending

- This skill **models and explains**; it never recommends an action, never states the
  customer qualifies (or not) for credit, and never guarantees a balance. Those are advisory
  or lending-decision activities that require a licensed human or an authorized decision
  system — route to them with the `forecast_id`.

## Duplicate-execution prevention

- The skill computes scenarios and drivers **once** and emits a durable `forecast_id`;
  downstream skills reuse that artifact rather than recomputing.
- It must not cross into eligibility, advice, or posting — those belong to the human and the
  downstream skills.
