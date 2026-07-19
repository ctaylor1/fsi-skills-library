---
name: retirement-income-scenario-modeler
description: >-
  Build a deterministic retirement-income projection: a year-by-year decumulation model
  from retirement to a longevity horizon that inflates spending, pays guaranteed income
  (Social Security, pension) net of approved taxes, funds the after-tax spending gap from
  taxable, tax-deferred, and tax-free accounts in a documented withdrawal order, and rolls
  balances forward across base / favorable / adverse scenarios modelling sequence and
  longevity risk. Every year ties out, every assumption is sourced, and results are a RANGE.
  Use when a financial planner or retirement specialist asks to model retirement income,
  spending, inflation, longevity, taxes, sequence risk, or withdrawal strategies with
  scenario ranges and tie-outs. HARD BOUNDARY: models and explains only; NEVER guarantees
  income or that assets will last, NEVER gives personalized investment, tax, insurance, or
  legal advice or recommends any withdrawal/claiming/product strategy, and NEVER approves,
  decides, files, trades, or writes a system of record.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, portfolio-accounting/OMS, planning-engine, product-data, disclosures/restrictions, and approved-tax-assumption MCP integrations, plus versioned retirement-modeling config (all read-only).
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Financial planner / retirement specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Retirement Income Scenario Modeler

## Purpose and outcome
Given a household's retirement inputs — balances by tax treatment, expected returns,
spending need, inflation, guaranteed income streams, approved tax assumptions, and a
withdrawal strategy — build a **deterministic, source-linked decumulation projection**:
year by year from the retirement age to a planning (longevity) horizon, inflate spending,
pay guaranteed income net of tax, fund the remaining after-tax spending gap from the
portfolio in a documented withdrawal order, roll each account forward at its scenario
return, and record where the plan runs short. The output is a **range** across
**base / favorable / adverse** scenarios (the adverse case can carry an explicit early
return sequence, so sequence-of-returns risk is modelled, not hand-waved) — every figure
tied out and every assumption sourced. A successful output lets a planner defend each number
to a client, supervisor, or suitability reviewer, and hands a reproducible model (`model_id`)
to downstream review, client-review, and rebalancing skills. The **planning recommendation
and any decision stay with a licensed human and the client.**

## Use when
- "Model this client's retirement income from 65 to 95 with base, favorable, and adverse cases."
- "Show sequence-of-returns and longevity risk on this plan as a range, with the tie-outs."
- "Fund the spending gap from taxable, then IRA, then Roth and show taxes and depletion year."
- "Which assumptions drive the shortfall, and where does each one come from?"
- A planner needs a defensible, reproducible income projection to anchor a plan or review.

## Do not use
- The user wants a **recommendation, a guarantee, or a decision** ("should they retire /
  claim now / buy this annuity?", "tell them it will last") → out of scope; build the range
  and route the judgment to a licensed advisor + client (see
  [references/handoffs.md](references/handoffs.md)).
- **Personalized investment, tax, insurance, or legal advice** → licensed-human matter.
- **Goal on-track measurement** against stated targets → `financial-goal-progress-analyzer`.
- **Objectives / constraints / risk-tolerance policy** → `investment-policy-statement-builder`.
- **Suitability / Reg BI evidence review** of a recommendation → `suitability-reg-bi-reviewer`.
- Turning the funding plan into **trades** → `portfolio-rebalancing-assistant` (R4, gated).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills supply goals,
objectives, and the account data; this skill emits a tied-out projection with a durable
`model_id`, `inputs_hash`, and `config_version`; downstream review, client-review, and
rebalancing skills consume it without rebuilding it. It must not duplicate their
recommendation, suitability, delivery, or trade-execution steps.

## Inputs and prerequisites
- **Household identifier** (de-identified) and a **valuation date** (anchors balances and rates).
- **Ages**: `current_age`, `retirement_age` (>= current age), `horizon_age` (> retirement age,
  the longevity/planning horizon). The projection runs the **decumulation phase** only —
  pre-retirement accumulation is out of scope (see `financial-goal-progress-analyzer`).
- **Spending**: `annual_need` (after-tax, in first-retirement-year dollars), `inflation`,
  and an approved `guaranteed_income_tax_rate` — each as `{value, provenance, citation}`.
- **Accounts** (`taxable` / `tax_deferred` / `tax_free`): `balance`, `expected_return`, and an
  approved `effective_tax_rate`, each sourced.
- **Guaranteed income** streams (Social Security, pension): `annual_amount`, `start_age`, `cola`.
- **Withdrawal**: `strategy` (`spending_gap` default, or `fixed_pct`), `order`, and any strategy
  parameters; **scenario_adjustments** for favorable/adverse (return/inflation deltas and an
  optional per-account `return_sequence`). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to CRM, portfolio accounting/OMS, the planning engine, product/disclosure data,
  and the versioned retirement-modeling config (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Custodial/portfolio-accounting
positions are the anchor for balances; the planning engine and client file supply spending
and guaranteed-income figures; the **approved capital-market and tax assumption set**
(versioned config) supplies returns, inflation, effective tax rates, and scenario deltas.
An assumption is only as good as its source — **cite every one with a date**; a custodial
balance outranks an estimate, and conflicts are recorded as explicit sourced overrides.
Returns, inflation, and tax rates are **approved assumptions, not the skill's judgment**, and
are never bent to make a plan "succeed".

## Workflow
1. **Scope** — confirm household, valuation date, currency/units, ages and horizon, accounts,
   guaranteed income, withdrawal strategy and order, and the scenario deltas; load balances
   and the approved assumption set.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors, note warnings (missing provenance, negative real return, high spending/assets
   ratio, very long horizon, missing a favorable/adverse case).
3. **Build the model (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): project each year
   for base / favorable / adverse — inflate spending, pay guaranteed income net of tax, fund
   the after-tax gap in withdrawal order (grossing up per account tax rate), roll balances
   forward at scenario returns, and record shortfalls, depletion age, and per-scenario tie-outs.
4. **Read the checks** — confirm every tie-out passes, scenarios are monotonic (terminal value
   adverse ≤ base ≤ favorable; shortfall favorable ≤ base ≤ adverse), and every assumption is
   in the register with provenance + citation.
5. **Write the pack** — a plain-language narrative of the assumptions, the withdrawal logic,
   the scenario **range**, the depletion/shortfall behavior, and the standing disclaimer. No
   recommendation, guarantee, or decision.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check independently re-derives the tie-outs (per-account balance
roll-forward and year-to-year continuity; the funding identity; the tax identity; portfolio
totals; non-negativity) — the same independent re-derivation the engine runs to populate each
scenario's `tieouts` and `model_checks.all_tieouts_ok`, so those flags reflect a real check
rather than a self-comparison. On top of its own re-derivation, the output check also **fails
closed if the pack self-reports a tie-out failure** (`all_tieouts_ok` false, or any scenario
`tieouts.*_ok` false). It further confirms scenario monotonicity on terminal value and
shortfall, requires provenance + citation on every assumption and `model_id` + `inputs_hash`,
screens the narrative for advice / guarantee / regulated-decision / closure / filing language,
and requires the disclaimer. **Fail closed on any miss.**

## Human approval
`required` (R3 decision support): the model is **evidence for a human decision**, never the
decision. A licensed advisor and the client must adjudicate — with a suitability / Reg BI
review where a recommendation follows — before any plan change, claiming election, product
purchase, trade, or write to the CRM / book of record. The skill takes **no action**, makes
**no regulated decision**, closes **no case**, files **nothing**, and writes **no system of
record**.

## Failure handling
- **Missing/non-numeric input** (age, balance, spending, rate) → `validate_input` errors; do
  not guess.
- **`horizon_age <= retirement_age`** or **`retirement_age < current_age`** → error; fix the
  age frame before projecting.
- **Unsourced assumption** → warned on input, **rejected** on output; every number needs a source.
- **Non-monotonic scenarios** → the deltas or a return sequence are inconsistent; stop and
  surface it rather than shipping an incoherent range.
- **Plan depletes** (shortfall before the horizon) → this is a **valid, important result**, not
  an error: report the depletion age and shortfall; never hide it or tune assumptions to erase it.
- **Conflicting sources** → keep the custodial/anchor figure, record the estimate as a sourced
  override, cite both.
- **Tool timeout** → return the scenarios computed so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — household (masked), valuation date, currency/units, ages/horizon, withdrawal
   strategy, and the base / favorable / adverse **range** (terminal portfolio value, funded
   years, depletion age if any).
2. **Projection** — per scenario: the year-by-year table (age, inflated spending, guaranteed
   income gross/net, per-account begin → withdrawal → return → end, taxes, funded, shortfall,
   surplus, portfolio begin/end).
3. **Assumptions register** — every spending, return, tax, guaranteed-income, and withdrawal
   assumption with `provenance` + `citation`.
4. **Model checks** — the tie-out results and scenario monotonicity.
5. **Machine-readable** — the full model JSON with `model_id`, `inputs_hash`, and
   `config_version` for downstream skills.
6. **Standing disclaimer** — "Illustrative retirement-income projection for planning purposes
   only, expressed as a range across deterministic scenarios; not a guarantee of future income,
   returns, or that assets will last, and not a probability of success. Not investment, tax,
   insurance, or legal advice and not a recommendation to adopt any withdrawal, claiming, or
   product strategy. Outputs depend entirely on the stated assumptions, which a qualified human
   must review; any recommendation or decision requires licensed-advisor and client adjudication."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
Highly Confidential (customer NPI/PII). A retirement plan embeds financial, health-adjacent
(longevity), and family data — treat the model, its inputs, and `model_id` as need-to-know,
and use de-identified household identifiers in artifacts. Retain the model, its assumptions
register, and `config_version` per records policy; log the read and any advisor adjudication.
Never exfiltrate client NPI.

## Gotchas
- **A projection is not a plan, and a range is not a guarantee.** Terminal values are
  conditional on the stated assumptions; never state or imply that income or assets are
  guaranteed to last, or quote a "probability of success" as a promise.
- **Sequence-of-returns risk is about order, not average.** The same average return with poor
  early years can deplete a plan that a smooth path would sustain — model the adverse case with
  an explicit early `return_sequence`, not just a lower mean.
- **Longevity dominates.** Extending the horizon a few years often flips a plan from funded to
  short; state the horizon age and treat it as an assumption, not a fact.
- **Withdrawal order and taxes interact.** Grossing up a net need at different account tax rates
  changes how fast the portfolio drains; the order is a documented assumption, not advice.
- **Approved assumptions are a versioned contract.** Returns, inflation, and tax rates come from
  the config; never tune them to make a plan "work" or to reach a wanted answer.
- **Depletion is a finding, not a failure.** Report it plainly and route the response to a human.
