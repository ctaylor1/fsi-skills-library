# Adjacent-Skill Handoffs — portfolio-cashflow-liquidity-forecaster

This skill produces a source-linked **dated liquidity cash-flow forecast** (`forecast_id`) — the
bucketed ladder, per-scenario closing-balance paths, any projected-shortfall bucket, tie-outs, an
assumptions log, and optional reconciliation — and stops. It does not choose a scenario, model
stressed liquidation, determine a breach, recommend or take any liquidity action, or deliver the
forecast anywhere.

## Upstream (feed this skill)

| Upstream source/skill | Provides | Handoff artifact |
| --------------------- | -------- | ---------------- |
| Transfer agent / custodian / collateral / ops systems | The sourced cash flows and opening cash | Dated cash-flow list + opening balance |
| `portfolio-exposure-analyzer` | Holdings/exposure context behind the flows and the book being forecast | Position/exposure context |
| Liquidity-risk analyst | The scenario set (multipliers, date shifts) and reconciliation targets | Analyst-supplied scenarios |

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `liquidity-stress-analyzer` | Stressed-liquidation lens — liquidation horizons, market-impact/cost, redemption coverage under an ADV-participation model (this skill does **not** model liquidation). |
| `counterparty-exposure-monitor` | Counterparty/settlement/collateral limit context behind collateral flows. |

## Downstream (consume this skill's `forecast_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `liquidity-stress-analyzer` | The forecast shows a projected shortfall and the analyst wants the stressed-liquidation view | `forecast_id` + shortfall bucket |
| `investment-committee-memo-builder` | The forecast becomes evidence in a committee memo | `forecast_id` + scenario summary |
| `board-committee-pack-builder` | Liquidity section of a board/committee pack | `forecast_id` + ladder summary |
| `mandate-compliance-monitor` | A mandate/regulatory liquidity-bucket rule must be tested against the flows | `forecast_id` + bucketed flows |

## Distinct-territory routing (do not conflate)

- **`liquidity-stress-analyzer`** (Asset Management, R2) — *stressed liquidation*: how long to
  liquidate, market impact, redemption coverage. This forecaster hands off stressed-liquidation
  work here; it never models liquidation itself.
- **`liquidity-risk-scenario-analyzer`** (Risk Management, R3) — *institution-wide treasury / ALM
  survival horizon* under regulatory stress with contingency-funding actions. This is a **distinct
  R3 skill** for treasury/ALM, not a portfolio/fund cash-flow forecast; route bank/treasury
  survival-horizon requests here, and do not treat it as the same thing as
  `liquidity-stress-analyzer`.

## Human / licensed-specialist handoff (no skill substitutes for it)

The **liquidity judgment** — which scenario to plan around, whether to raise cash or sell/liquidate
assets, what liquidity buffer to hold, and whether to gate or suspend redemptions — is **out of
scope** and belongs to the **liquidity-risk analyst, the portfolio manager, the liquidity risk
committee, and the dealing/execution desk or authorized systems**. This skill routes those
decisions to those humans; it never makes them. Personalized investment, trading, or tax advice is
likewise a licensed-human matter.

## Duplicate-execution prevention

- This skill builds and ties out the **dated forecast only**; it must not choose a scenario, model
  stressed liquidation, determine a breach, recommend or take a liquidity action, or deliver the
  forecast — those belong to humans and the skills above.
- Downstream skills reuse the `forecast_id` (with its `inputs_hash` and `config_version`) rather
  than rebuilding the ladder, so the same inputs produce the same numbers everywhere it is cited.
