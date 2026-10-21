# Adjacent-Skill Handoffs — portfolio-hedge-reviewer

This skill produces a neutral **hedge-analysis support packet** (`packet_id`, carrying the
durable `case_id`) — the portfolio's exposures/sensitivities, and for a human-defined set of
candidate hedges the residual exposure, coverage, supplied cost, and first-order scenario
P&L, in a comparison table with limitations — and stops. It **does not** select, recommend,
rank, or endorse a hedge, decide whether to hedge, or execute any trade, and it does not
deliver the packet anywhere.

## Upstream (feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `portfolio-exposure-analyzer` | Base-portfolio exposures/sensitivities by factor with lineage | Portfolio sensitivity set |
| `pricing-hedging-scenario-calculator` | Instrument-level pricing & sensitivities (rates/vol/spread/correlation/dividends/funding) for a hedge | Candidate-hedge sensitivities |
| `stress-test-scenario-designer` | Approved severe-but-plausible scenarios and their factor shocks | Scenario shock sets |
| `investment-reference-data-reviewer` | Instrument reference/analytics data behind the hedge specs | Enriched hedge instrument data |
| `investment-record-normalizer` | Normalized positions underlying the exposure set | Clean position set |

This skill **consumes** these; it does not re-derive base exposures, price instruments, or
invent scenarios.

## Parallel / cross-check (consume this skill's `packet_id`)

| Skill | Why |
| ----- | --- |
| `portfolio-stress-test-runner` | Full multi-factor / historical stress runs and driver attribution beyond first-order scenario P&L |
| `portfolio-risk-contribution-analyzer` | Marginal / total risk-contribution decomposition (vs this skill's exposure/coverage view) |
| `market-risk-limit-monitor` | Test the residual exposure against market-risk limits and produce escalation evidence |
| `investment-mandate-reviewer` | Test a proposed hedge against mandate, guideline, and restriction rules |
| `counterparty-exposure-monitor` / `margin-collateral-optimizer` | Derivative counterparty, collateral, and margin implications of a hedge |
| `transaction-cost-estimator` | Estimate the execution cost / market impact of a hedge (this skill only tabulates a supplied cost) |

## Downstream (consume this skill's `packet_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `investment-committee-memo-builder` | The comparison becomes evidence in an IC memo where the hedge decision is made by humans | `packet_id` + comparison summary |

## Human / licensed-specialist handoff (no skill substitutes for it)

The **hedge decision** — whether to hedge, which candidate to use, and how to size it — is a
**portfolio-manager / investment-committee judgment** and is out of scope; this skill routes
that decision to those humans and never makes it. **Execution** of any hedge or overlay
belongs to the **trading desk / OMS** and is likewise out of scope. Personalized investment,
legal, or tax advice is a licensed-human matter.

## Duplicate-execution prevention

- This skill computes and ties out the **comparison only**; it must not reach a selection,
  set a hedge ratio, price the instruments, run full stress grids, decompose risk
  contributions, test limits, estimate transaction cost, or deliver/execute anything — those
  belong to the adjacent skills and humans above.
- Downstream and parallel skills reuse the `packet_id` (with its `inputs_hash`,
  `config_version`, and `model.version`) rather than recomputing the exposures, so the same
  assumptions produce the same numbers everywhere the packet is cited.


## Phase 4 supplied full-repricing extension

For explicitly selected `advanced-derivatives`, use [the separate advanced contract](advanced-derivatives.md). Preserve full-book engine/benchmark binding and the no-fallback boundary; the first-order method above is not a complex derivative pricer.
