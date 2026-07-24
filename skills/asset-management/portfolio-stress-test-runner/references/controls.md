# Controls - portfolio-stress-test-runner

- **Risk tier:** R2 - analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` - required before the run is delivered to a risk or
  investment committee, attached to a board pack, or written to any risk system of record.
  No approval is needed for the analyst's own read.

## Prohibited (fail closed)

- No **invented, designed, edited, extended, or improvised scenario or shock**. Scenarios are
  consumed from an approved source (`stress-test-scenario-designer` or an approved scenario
  library), must be `approved: true`, and must carry a `scenario_set_id` and citation.
- No **investment recommendation or action instruction** - buy / sell / hold / hedge /
  rebalance / de-risk / trim / rotate / exit / overweight / underweight, or any allocation
  advice or "the loss implies you should ..." framing.
- No **risk-limit setting, breach-action mandate, or capital determination** - these are
  control decisions for the risk function (`market-risk-limit-monitor` compares to limits and
  escalates).
- No **run presented with a failing tie-out or a reconciliation break** against the approved
  engine.
- No **assumption without provenance**; no **scenario without approval**; no formula,
  tolerance, rounding, or attribution rule bent to reach a wanted loss.
- No **guarantee** of a loss, return, or downside protection.

## Required output screens (`scripts/validate_output.py`)

- Every scenario is marked **approved** and every `scenario-definition` register entry carries
  `approved: true` plus provenance and citation (HARD BOUNDARY - never invent scenarios).
- Every scenario ties out: `sum(position P&L) == sum(factor P&L) == scenario_pnl`; each
  position P&L equals the sum of its factor contributions; `stressed_value == base + P&L`.
- Where an approved-engine total is supplied, the computed total reconciles within tolerance
  (a break fails closed).
- Every `assumptions_register` entry has a non-empty `provenance` **and** `citation`.
- `run_id` and `inputs_hash` present (reproducibility).
- No investment-advice / recommendation / hedge-rebalance-derisk / risk-limit / invented-
  scenario language in the author narrative (regex screen; the standing disclaimer is stripped
  first so it cannot self-trip).
- Standing disclaimer present: "Illustrative stress-test run for analytical purposes only; not
  investment advice, not a recommendation to buy, sell, hold, hedge, rebalance, or de-risk any
  position or portfolio, and not a risk-limit or capital determination. Results execute
  human-approved scenarios against the stated portfolio and risk model and depend entirely on
  those approved scenario definitions, position data, and factor sensitivities, which a
  qualified human must review."

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Portfolio holdings, factor
  sensitivities, and stress results can be market-sensitive and client-confidential; treat the
  run, its inputs, and its `run_id` as need-to-know.
- Respect information barriers; do not move confidential holdings or results across a wall.
- Retain the run, its assumptions register, and the `scenario_set_version` / `model_version` /
  `config_version` per records policy; log the read and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the run to the exact numeric assumptions and approved scenario shocks; the
`scenario_set_version`, `model_version`, and `config_version` bind the scenarios, sensitivity
model, and conventions. Re-running the same inputs reproduces the same `run_id` and the same
numbers. Changing any assumption changes the hash - the audit trail shows what moved.

## Separation of duties

Designing the scenario (`stress-test-scenario-designer`, R3), running it (this skill, R2),
comparing losses to limits and escalating (`market-risk-limit-monitor`), and deciding any
investment or risk action (portfolio manager / CIO / risk committee) are **distinct** roles.
The run is a draft analytical input to a human's judgment, never a substitute for it, and it
takes no action.
