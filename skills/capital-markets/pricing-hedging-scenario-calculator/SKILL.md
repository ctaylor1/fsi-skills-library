---
name: pricing-hedging-scenario-calculator
description: >-
  Compute illustrative scenario P&L and a delta-neutral hedge ratio for a rates/linear position
  from documented parameters (position DV01, direction, rate-shock scenarios, hedge-instrument
  DV01) — showing unhedged P&L per scenario, the hedge units needed to neutralize DV01, and the
  residual — as a scenario worksheet for a structuring analyst. Use when an analyst asks to "run
  the pricing scenarios", "what's the P&L if rates move 25bp", "size the hedge for this position",
  or "build the hedging scenario worksheet". HARD BOUNDARY: R3 model/decision-support only — it
  produces an illustrative, linear estimate; it NEVER quotes or sets a firm price, and NEVER
  executes, puts on, or instructs a trade or hedge; the desk owns pricing and execution. Routes
  transaction-cost estimation to transaction-cost-estimator.
license: MIT
compatibility: Amazon Quick Desktop; requires position/risk parameters and reference-data MCP integrations (all read-only). Deterministic stdlib-only linear computation.
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Structuring analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Pricing & Hedging Scenario Calculator

## Purpose and outcome
Given a position's DV01, direction, a set of rate-shock scenarios, and a hedge instrument's DV01,
deterministically compute the illustrative unhedged P&L per scenario, the delta-neutral hedge
units, and the residual DV01 after hedging. A successful output is a linear scenario worksheet a
structuring analyst reviews — the firm price and any execution remain the desk's.

## Use when
- "Run the pricing scenarios", "what's the P&L if rates move 25bp".
- "Size the hedge for this position", "build the hedging scenario worksheet".
- An analyst needs a consistent, reproducible scenario/hedge-sizing estimate.

## Do not use
- The user wants a **firm price/quote** or to **execute/put on** a trade or hedge → out of scope;
  the desk acts.
- The user wants a **transaction-cost estimate** for filling size → route to
  `transaction-cost-estimator`.
- The instrument needs **full non-linear (option) revaluation** → escalate; this skill is linear
  (DV01) only.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a scenario worksheet with a durable
`scenario_id`; it does not price firmly or execute.

## Inputs and prerequisites
- The **trade** (position_dv01, direction), **scenarios** (shock_bp), and **hedge**
  (hedge_dv01_per_unit). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Linear DV01 approximation; parameters are documented inputs. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Risk parameters come from the risk
system; the worksheet records the parameters used and is explicit that it is a linear estimate.

## Workflow
1. **Validate input** — run `validate_input`; confirm DV01, direction, scenarios, and hedge DV01.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per scenario, P&L =
   sign(direction) × position_dv01 × shock_bp; hedge_units = position_dv01 / hedge_dv01_per_unit;
   residual_dv01.
3. **Assemble the worksheet** — scenario P&L table, hedge sizing, residual, parameters used.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for the
   per-scenario P&L identity, hedge-sizing tie, the no-firm-price/no-execution screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a scenario P&L does not equal the linear
identity, or the text contains firm-price/execution language, **fix or fail closed**.

## Human approval
`required`: no firm price/quote and no execution/hedge placement without the authorized desk. The
skill only estimates scenarios and hedge sizing.

## Failure handling
- **Missing DV01/parameters** → fail closed; do not assume a risk figure.
- **Zero hedge DV01** → flag; do not divide; hedge sizing not-computable.
- **Large shocks / non-linear instruments** → state the linear-approximation limitation; do not
  present a linear P&L as exact for a convex/optioned position.
- **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — trade id, position DV01, direction, number of scenarios.
2. **Scenario P&L** — per scenario: shock_bp and illustrative P&L.
3. **Hedge sizing** — hedge units, side, residual DV01 after hedge.
4. **Machine-readable** — scenarios + hedge + `scenario_id`.
5. **Standing disclaimer** — "Illustrative linear scenario analysis only; not a firm price, a
   quote, or an instruction to execute or hedge. Nothing has been priced or traded."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Retain worksheet + parameters. Log read + external-delivery approval. Never
exfiltrate position data across the wall.

## Gotchas
- **Linear ≠ exact.** DV01 P&L is a first-order estimate; large moves and optionality need full
  revaluation — say so.
- **Hedge sizing is a ratio, not an order.** Report units and side; never "put on the hedge".
- **Sign discipline**: a long position loses as yields rise; confirm the direction convention.
- **Never state a firm price or imply execution.**
