# Adjacent-Skill Handoffs — investment-policy-statement-builder

Drafting the IPS (this skill), reviewing its suitability, comparing proposals, and trading to its
targets are **separate control activities** with different entitlements, evidence, and approvals.
This skill emits a durable `ips_id` + draft package; it must not perform the review or the trading.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `financial-goal-progress-analyzer` | Goal shortfalls / planning levers that inform objectives and return needs | Documented objectives + assumptions |
| `retirement-income-scenario-modeler` | Income/withdrawal ranges that inform time horizon, liquidity, and return objective | Modeled ranges (not guarantees) |
| `client-review-preparer` | Review context / life events that trigger an IPS build or refresh | Review brief + change triggers |

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `suitability-reg-bi-reviewer` | The drafted allocation/recommendation needs a suitability / Reg BI and supervision review (never approved here) | `ips_id` + draft package + source map |
| `portfolio-proposal-comparator` | The client wants competing allocation proposals weighed against the IPS constraints | `ips_id` + strategic allocation + constraints |
| `portfolio-rebalancing-assistant` | A portfolio must be moved toward the IPS targets (R4, advisor + client authorization) | `ips_id` + target allocation + bands |
| `advisor-follow-up-assistant` | Client-facing notes, disclosures, or CRM updates around the IPS are needed | `ips_id` + approved draft |
| `senior-investor-protection-screener` | Senior-investor, diminished-capacity, or trusted-contact concerns surface during drafting | `ips_id` + flagged concern evidence |

## Non-catalog / human handoffs

- **Advisor** owns the recommendation; **compliance / supervisor** owns the suitability and
  supervision sign-off; **client** owns acceptance by signature. These are human roles, captured in
  the draft's approval block as `pending` — no catalog skill grants them.
- **Custodian delivery / e-signature / document management** are operations-team steps performed
  out-of-band after human approval; this skill never initiates them.

## Duplicate-execution prevention

- This skill **does not** review suitability, compare proposals, or trade — those belong downstream.
- The suitability reviewer consumes the `ips_id`/draft rather than re-drafting the IPS.
- A refresh supersedes the prior draft under the same `ips_id` lineage and records what changed;
  it does not spawn a parallel, conflicting IPS.
