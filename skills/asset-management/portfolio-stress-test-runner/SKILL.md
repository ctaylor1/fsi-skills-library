---
name: portfolio-stress-test-runner
description: >-
  Execute human-approved historical and hypothetical stress scenarios against an approved
  portfolio and risk-factor model: apply each scenario's factor shocks through approved
  per-position sensitivities, compute the scenario P&L and stressed value, attribute drivers
  by position and by factor, reconcile to the firm's approved stress engine, and emit a
  reproducible run. Use when a portfolio-risk analyst asks to "run our approved stress
  scenarios", "stress this portfolio", "compute the P&L under the GFC or rate-shock scenario",
  or wants a driver attribution and engine reconciliation for a stress run. This skill runs and
  explains only; it NEVER invents, designs, or edits a scenario (scenarios come from
  stress-test-scenario-designer or an approved library and must be human-approved), NEVER
  issues an investment recommendation or a hedge / rebalance / de-risk instruction, and NEVER
  sets a risk limit or makes a capital determination — those are licensed-human / committee
  judgments.
license: MIT
compatibility: Amazon Quick Desktop; requires approved-portfolio (PMS/OMS), risk-factor-model, approved-scenario-library, approved-stress-engine, and versioned stress-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Portfolio-risk analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Portfolio Stress Test Runner

## Purpose and outcome
Given an approved portfolio, an approved risk-factor sensitivity model, and a set of
**human-approved** stress scenarios, execute a **deterministic, reproducible stress run**:
apply each scenario's factor shocks through per-position sensitivities, compute the scenario
P&L and stressed value, attribute the drivers **by position and by factor**, and reconcile to
the firm's approved stress engine — every figure tied out and every input sourced. A
successful output lets a portfolio-risk analyst defend each loss and each driver to a
reviewer, risk committee, or investment team, and hands a reproducible run (`run_id`) to
downstream limit-monitoring and reporting. **Scenario design and any investment or risk action
stay with the appropriate humans / skills.**

## Use when
- "Run our approved stress scenarios against this portfolio and show the P&L."
- "Stress the portfolio under the approved 2008 GFC replay / +200bp rate scenario."
- "Attribute the stress loss by position and by factor."
- "Reconcile the stress run to the official risk-engine totals and give me the tie-outs."
- A portfolio-risk analyst needs a defensible, reproducible run to anchor a risk review.

## Do not use
- The user wants to **design, invent, edit, or improvise a scenario** ("make up a recession
  scenario", "add a shock", "what if we assumed...") → out of scope; scenario design belongs
  to `stress-test-scenario-designer` and must be human-approved before this skill runs it
  (see [references/handoffs.md](references/handoffs.md)).
- The user wants a **recommendation or action** ("how much should I sell?", "hedge the rate
  risk", "rebalance the book", "de-risk") → prohibited; run the scenarios and route the
  action decision to a licensed human / investment or risk committee.
- The user wants to **compare losses to limits and escalate breaches** → `market-risk-limit-monitor`.
- The user wants **exposure decomposition** (issuer/sector/country/duration) → `portfolio-exposure-analyzer`.
- The user wants **marginal/total risk contributions** → `portfolio-risk-contribution-packet`.
- The user wants a **full sensitivity grid** across shock magnitudes → `scenario-sensitivity-generator`.
- **Personalized investment advice**, a risk-limit change, or a capital determination →
  licensed-human / risk-function matter.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream `stress-test-scenario-designer`
supplies the approved scenario definitions and the portfolio/risk systems supply positions and
sensitivities; this skill emits a tied-out run with a durable `run_id`, `inputs_hash`,
`scenario_set_version`, `model_version`, and `config_version`; downstream limit/monitoring and
reporting steps consume it without re-running it. It must not design scenarios, recommend,
set limits, or deliver the run.

## Inputs and prerequisites
- **Portfolio identifier**, an **`as_of`** date, a **`run_date`**, base currency/units, and a
  **`portfolio_base_value`** that reconciles to the sum of position market values.
- **Positions** — each with `market_value`, `provenance`/`citation`, and `factor_exposures`
  mapping each risk factor to a `{sensitivity, convexity?, provenance, citation}` (sensitivity
  is P&L per unit factor shock, in currency).
- **Risk factors** — the approved factor taxonomy (`factor_id → {label, unit, provenance,
  citation}`); every exposed and shocked factor must be defined.
- **Scenarios** — each a **human-approved** definition: `approved: true`, `scenario_set_id`,
  `scenario_set_version`, `source` (an approved scenario source), `approval_ref`, `citation`,
  `type` (`historical`/`hypothetical`), and `shocks` (`factor_id → number`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Optional **`approved_engine_totals`** (`scenario_id → number`) to reconcile against, and a
  **`reconciliation_tolerance`**; `config_version` and `model_version`.
- Read access to the approved portfolio, risk-factor model, approved scenario library, and the
  approved stress engine (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The book-of-record portfolio is the
anchor for positions; the approved risk model supplies sensitivities; the approved scenario
library supplies the shocks; the approved engine supplies the reconciliation target; versioned
config supplies tolerance and conventions. **The scenarios are never authored here** — they
are consumed from an approved source and must be human-approved. Cite every input with a date;
a book-of-record figure outranks an estimate, and conflicts are recorded as explicit sourced
notes.

## Workflow
1. **Scope** — confirm portfolio, `as_of`/`run_date`, currency/units, the approved
   `scenario_set_id`/version, and the sensitivity `model_version`; load positions,
   sensitivities, and the approved scenarios.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors (unknown factors, non-numeric sensitivities/shocks, and any **un-approved or
   unsourced scenario** — the runner fails closed rather than run an invented scenario), note
   warnings (missing provenance, positions not reconciling to base value).
3. **Run the scenarios (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): apply each
   scenario's shocks through per-position sensitivities (first-order plus optional convexity),
   compute scenario P&L and stressed value, attribute by position and by factor, and reconcile
   to the approved engine where totals are supplied.
4. **Read the checks** — confirm every scenario ties out (position sum == factor sum ==
   scenario P&L; stressed value == base + P&L), every reconciliation is within tolerance, every
   scenario is approved, and every input is in the register with provenance + citation.
5. **Write the run** — a plain-language narrative of each scenario's loss, stressed value, and
   top position/factor drivers, with explicit sources and the standing disclaimer. No
   recommendation, action, limit, or invented scenario.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check independently re-derives every tie-out (position and factor
attributions each reconcile to `scenario_pnl`; each position reconciles to its factor
contributions; stressed value == base + P&L), re-checks engine reconciliation, requires every
scenario to be **approved** and every assumption to carry provenance + citation, requires
`run_id` + `inputs_hash`, screens the narrative for advice / recommendation / action / limit /
invented-scenario language, and requires the disclaimer. **Fail closed on any miss.**

## Human approval
`external-delivery`: human review and approval are required before the run is delivered to a
risk or investment committee, attached to a board pack, or written to any risk system of
record. No approval is needed for the analyst's own read. The skill takes **no action**, makes
**no risk or investment decision**, and **authors no scenario**.

## Failure handling
- **Un-approved / unsourced / invented scenario** → `validate_input` errors and
  `validate_output` rejects; **do not run it**. Route scenario design to
  `stress-test-scenario-designer`.
- **Unknown risk factor** (exposure or shock references a factor not in the taxonomy) →
  `validate_input` errors; do not guess a factor.
- **Non-numeric sensitivity / shock** → `validate_input` errors; do not guess a value.
- **Reconciliation break** (computed total disagrees with the approved engine beyond
  tolerance) → fail closed; surface the break rather than presenting a run that disagrees with
  the system of record.
- **Positions not reconciling to base value** → warned; confirm the holdings feed before use.
- **Unsourced input** → warned on input, **rejected** on output; every input needs a source.
- **Tool timeout** → return the scenarios computed so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — portfolio (masked as needed), `as_of`/`run_date`, currency/units, base value,
   and per scenario the P&L, `pnl_pct`, and stressed value.
2. **Per scenario** — attribution by position (P&L and per-factor contributions, largest loss
   first), attribution by factor (P&L, largest absolute first), and the engine reconciliation.
3. **Scenario-set provenance** — for each scenario: `scenario_set_id`, version, source,
   `approval_ref`, and citation.
4. **Assumptions register** — every scenario (with `approved`), position, and factor
   sensitivity with `provenance` + `citation`.
5. **Run checks** — tie-out results, reconciliation status, and the all-approved flag.
6. **Machine-readable** — the full run JSON with `run_id`, `inputs_hash`,
   `scenario_set_version`, `model_version`, and `config_version` for downstream skills.
7. **Standing disclaimer** — "Illustrative stress-test run for analytical purposes only; not
   investment advice, not a recommendation to buy, sell, hold, hedge, rebalance, or de-risk any
   position or portfolio, and not a risk-limit or capital determination. Results execute
   human-approved scenarios against the stated portfolio and risk model and depend entirely on
   those approved scenario definitions, position data, and factor sensitivities, which a
   qualified human must review."

See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. Portfolio holdings, factor sensitivities, and stress results can be
market-sensitive and client-confidential — treat the run, its inputs, and its `run_id` as
need-to-know and respect information barriers. Retain the run, its assumptions register, and the
`scenario_set_version` / `model_version` / `config_version` per records policy; log the read and
any external-delivery approval. Never exfiltrate confidential holdings or results.

## Gotchas
- **A stress run is not a recommendation.** A loss under a scenario is conditional on approved
  shocks and sensitivities; it is never a buy/sell/hedge/rebalance/de-risk instruction, a limit,
  or a capital call.
- **Never invent a scenario.** If a scenario is not approved and sourced, the run fails closed.
  Reaching for a "worst case" the firm has not approved is exactly the prohibited behavior.
- **Units must match.** A shock's unit (relative return, absolute bp) must match the sensitivity
  it multiplies; mixing them silently corrupts the P&L. The risk model defines both; the runner
  applies them.
- **Reconcile, don't override.** If the computed total disagrees with the approved engine,
  surface the break — do not tune tolerance, rounding, or a sensitivity to make it tie.
- **Convexity is second-order.** For large rate/spread shocks the linear term alone understates
  the move; the optional `0.5 * gamma * shock^2` term is applied consistently in both
  attributions so the walk still ties.
- **Attribution order is presentation, not advice.** "Largest loss first" ranks drivers; it
  does not rank actions.
