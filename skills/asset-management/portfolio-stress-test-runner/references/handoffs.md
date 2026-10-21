# Adjacent-Skill Handoffs - portfolio-stress-test-runner

This skill **executes** human-approved stress scenarios against an approved portfolio and
risk model, computes each scenario's P&L, attributes the drivers by position and by factor,
reconciles to the approved engine, and stops. It does not design scenarios, does not
recommend or mandate any action, and does not deliver the run anywhere.

## Upstream (feed this skill)

| Upstream skill / source | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| `stress-test-scenario-designer` | The **approved scenario definitions** - shocks, transmission assumptions, type, and reverse-stress thresholds | Approved `scenario_set_id` + `scenario_set_version` with shocks and approval reference |
| `portfolio-holdings-summarizer` / PMS book of record | The approved portfolio positions and market values | Positions + base value as-of a date |
| Approved risk-factor model (risk engine) | Per-position factor sensitivities/convexities and the factor taxonomy | Sensitivity set with `model_version` |

Scenario **design** - authoring severe-but-plausible narratives, transmission channels,
variable paths, and reverse-stress thresholds - belongs to `stress-test-scenario-designer`
(R3). This skill never authors a scenario; it consumes an approved one.

## Parallel / cross-check

| Skill | Why |
| ----- | --- |
| `portfolio-exposure-analyzer` | Exposure decomposition (issuer/sector/country/duration) as context for the stressed drivers |
| `portfolio-risk-contribution-analyzer` | Marginal/total risk contributions - a complementary risk lens to scenario P&L |
| `scenario-sensitivity-generator` | Expand a single approved scenario into a sensitivity grid across shock magnitudes |

## Downstream (consume this skill's `run_id`)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `market-risk-limit-monitor` | Compare the stress losses to approved limits and raise an escalation on a breach | `run_id` + per-scenario `scenario_pnl` and stressed value |
| `portfolio-characteristics-change-monitor` | Track how stressed risk evolves versus prior runs | `run_id` + scenario summary |

Committee, board-pack, and risk-system reporting are **human-approved delivery steps**, not a
skill this package performs; the run is a reproducible input those steps cite by `run_id`.

## Human / licensed-specialist handoff (no skill substitutes for it)

Two decisions are **out of scope** and belong to humans:

- **Scenario design and approval** - the risk methodology owners / `stress-test-scenario-
  designer` author and the risk committee approves the scenarios. This skill only runs
  approved ones.
- **The investment or risk action** - whether a stress loss implies hedging, rebalancing,
  de-risking, changing an allocation, or setting a limit is a **portfolio manager / CIO /
  risk-committee** judgment. This skill routes that decision to those humans; it never makes
  it, and it never gives personalized investment advice.

## Duplicate-execution prevention

- This skill **runs and attributes** approved scenarios only; it must not design a scenario,
  reach a recommendation, set a limit, or deliver the run - those belong to the skills and
  humans above.
- Downstream skills reuse the `run_id` (with its `inputs_hash`, `scenario_set_version`,
  `model_version`, and `config_version`) rather than re-running the scenarios, so the same
  approved inputs produce the same numbers everywhere the run is cited.
