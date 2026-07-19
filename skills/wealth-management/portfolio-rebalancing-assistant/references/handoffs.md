# Adjacent-Skill Handoffs — portfolio-rebalancing-assistant

This skill owns the **plan → validate → authorize → execute → verify → audit** lifecycle for
a proposed rebalance. It does not analyze drift or exposure on its own, does not make a
suitability determination, and does not opine on tax strategy.

## Upstream (hands context in)

| Upstream source | Handoff artifact |
| --------------- | ---------------- |
| `investment-policy-statement-builder` | Target model, allocation, and drift bands (`model_id`, `policy_version`) |
| `portfolio-holdings-summarizer` / `portfolio-exposure-analyzer` | Current holdings, weights, and exposure context |
| `portfolio-risk-diversification-check` / `financial-goal-progress-analyzer` | Drift and goal signals indicating a rebalance is warranted |
| `portfolio-proposal-comparator` | A chosen target proposal to rebalance toward |

## Downstream / lateral (route instead of acting)

| Skill | When |
| ----- | ---- |
| `suitability-reg-bi-reviewer` | The proposed changes need a suitability / Reg BI best-interest review before authorization |
| `senior-investor-protection-screener` | The client is a senior or otherwise vulnerable investor and trading may need enhanced protection |
| `employee-trading-preclearance-assistant` | The account or symbols require employee/access-person preclearance |
| `best-execution-reviewer` | Best-execution review of how the orders were routed and filled |
| `post-trade-settlement-monitor` | After execution, monitor settlement and breaks |
| `mandate-compliance-monitor` | Ongoing mandate / restriction monitoring beyond this single plan |
| `advisor-follow-up-assistant` | Draft the client-facing follow-up once trades are authorized/placed |
| `retirement-income-scenario-modeler` | The request is really a withdrawal/income modeling question, not a rebalance |

## Human / licensed-specialist handoffs (no catalog skill)

- **Personalized tax advice** (specific-lot strategy, harvest sizing beyond the approved
  assumption set) → licensed tax advisor. This skill only reports estimated realized
  gain/loss under the approved tax-assumption version.
- **Suitability sign-off and the investment recommendation itself** → the licensed advisor.
- **Over-limit, restricted, irreversible, or policy-exception trades** → human trading desk /
  compliance authority; this skill fails closed and escalates rather than planning them.

## Duplicate-execution prevention

- Only this skill submits the rebalance orders; upstream analysis skills must not also trade.
- Execution is keyed by `plan_id` + step idempotency keys — re-invocation never double-submits.
- If another workflow already rebalanced the account, the precondition check fails and this
  skill halts rather than re-submitting.
