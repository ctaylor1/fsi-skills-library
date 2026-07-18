---
name: three-statement-model-builder
description: >-
  Build a source-linked, integrated three-statement operating model: a driver-based income
  statement, balance sheet, and cash-flow statement that link so the balance sheet ties every
  year and cash-flow cash reconciles to the balance sheet, with debt, PP&E, and
  working-capital schedules and base / upside / downside scenarios — every line re-derived
  from sourced assumptions and every tie-out checked. Use when an investment-banking or
  research analyst asks to "build a three-statement model", "project the income statement,
  balance sheet, and cash flow", "link the three statements", or "make the model balance".
  This skill models only; it NEVER issues an investment recommendation (buy/sell/hold), price
  target, fair-value verdict, or fairness opinion, NEVER discounts the model to a valuation
  (that is dcf-modeler's scope), and NEVER gives personalized investment, legal, accounting,
  or tax advice — those are licensed-human judgments.
license: MIT
compatibility: Amazon Quick Desktop; requires filing-intelligence, market/financial-data, approved operating-model, research-corpus, and approved-calculation MCP integrations, plus versioned model config (all read-only).
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Investment-banking / research analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Three-Statement Model Builder

## Purpose and outcome
Given a company's base-year financials and an explicit set of forecast drivers, build a
**deterministic, source-linked three-statement operating model**: project a linked income
statement, balance sheet, and cash-flow statement, produce the supporting debt, PP&E, and
working-capital schedules, and generate **base / upside / downside** scenarios — with the
**balance sheet tying every year**, the **cash-flow statement reconciling to balance-sheet
cash**, and every assumption sourced. A successful output lets an analyst defend each number
to a reviewer or deal team, and hands a reproducible model (`model_id`) to downstream
valuation, memo, pitch, and review skills. The **valuation and investment judgment stay with
a licensed human.**

## Use when
- "Build a three-statement model / integrated operating model for this company."
- "Project the income statement, balance sheet, and cash flow from these drivers."
- "Link the three statements and make sure the balance sheet balances."
- "Give me base, upside, and downside operating cases with the schedules and tie-outs."
- "Show the driver assumptions and where each one comes from."
- An analyst needs a defensible, reproducible operating model to feed a valuation.

## Do not use
- The user wants a **recommendation, price target, fair-value verdict as a decision, or
  fairness opinion** ("should I buy?", "what's it worth?") → out of scope; build the model
  and route the judgment to a licensed analyst / investment committee (see
  [references/handoffs.md](references/handoffs.md)).
- **Discount the model to a value** (WACC, terminal value, value per share) → `dcf-modeler`.
- **Relative valuation** (trading comps / precedents) → `comps-analysis-builder`.
- **Return-based / transaction** models → `lbo-model-builder` or `merger-model-builder`.
- Full **sensitivity/tornado grids** beyond the three cases → `scenario-sensitivity-generator`.
- **Personalized investment, legal, accounting, or tax advice** → licensed-human matter.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills supply the base-year
financials and drivers; this skill emits a tied-out operating model with a durable `model_id`,
`inputs_hash`, and `config_version`; downstream valuation, memo, pitch, and review skills
consume it without rebuilding it. It must not discount the model, reach a recommendation, or
deliver it — those belong to humans and downstream skills.

## Inputs and prerequisites
- **Company identifier** and an **as_of** date (anchors the base period and driver vintage).
- **Base-year income statement** (revenue, cogs, opex, depreciation, interest, tax, net
  income) and **base-year balance sheet** (cash, receivables, inventory, other current
  assets, net PP&E, other assets, payables, other current liabilities, debt, other
  liabilities, equity) from filed financials.
- **Forecast drivers** (14) — revenue growth, gross margin, opex %, depreciation rate, capex
  %, DSO/DIO/DPO, other-current-asset/liability %, tax rate, interest rate, debt repayment,
  dividend payout — each as `{value, source}`.
- **forecast_years** and optional **scenarios** (revenue-growth and gross-margin deltas for
  base/upside/downside). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to filing-intelligence, market data, the approved operating model, and the
  versioned model config (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filed financials are the anchor for
the base year; management guidance and the approved operating model supply forward drivers;
market data supplies financing terms; research/consensus gives sanity ranges; versioned config
supplies scenario deltas and conventions. A forecast driver is only as good as its source —
**cite every assumption with a date**; a filed number outranks an estimate, and conflicts are
recorded as explicit sourced drivers.

## Workflow
1. **Scope** — confirm company, as_of / base period, currency/units, forecast horizon, and
   scenario deltas; load base-year statements and drivers.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors, note warnings (missing source, base balance sheet that does not tie, out-of-range
   driver, long horizon).
3. **Build the model (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): project the income
   statement, drive the balance-sheet items, derive the cash-flow statement (cash is the
   plug), build the debt / PP&E / working-capital schedules, and produce base / upside /
   downside with per-year tie-outs. Interest and depreciation use **opening** balances, so the
   model is non-circular and reproducible.
4. **Read the checks** — confirm the balance sheet ties every year, cash reconciles, equity
   and PP&E roll-forwards hold, and scenario revenue is monotonic; every driver is sourced.
5. **Write the model pack** — a plain-language narrative of the drivers, the three statements,
   the schedules, and the scenario range, with explicit assumptions and their sources — and
   the standing disclaimer. No recommendation, target, valuation, or opinion.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check independently re-derives the tie-outs (balance-sheet identity, cash
tie, equity and PP&E roll-forwards from the stored statements), confirms scenario
monotonicity, requires a `source` on every assumption and the full required-driver set,
requires `model_id` + `config_version` + `inputs_hash`, screens the narrative for
advice/recommendation/target/rating language, and requires the disclaimer. **Fail closed on
any miss.**

## Human approval
`external-delivery`: human review and approval are required before the model is delivered to a
client, deal team, data room, or CRM, or written to any system of record. No approval is
needed for the analyst's own read. The skill takes **no action** and makes **no valuation or
investment decision**.

## Failure handling
- **Missing/non-numeric driver or statement line** → `validate_input` errors; do not guess.
- **Unsourced assumption** → warned on input, **rejected** on output; every driver needs a
  source.
- **Base balance sheet does not tie** → warned on input; the imbalance is carried honestly and
  `validate_output` fails closed on the identity — never silently plugged.
- **Non-monotonic scenarios** → the scenario deltas are inconsistent; stop and surface it
  rather than shipping an incoherent range.
- **Conflicting sources** → keep the filed anchor for the base year, record the estimate as a
  sourced driver, cite both.
- **Tool timeout** → return the years/scenarios computed so far with an explicit "incomplete"
  flag.

## Output contract
1. **Summary** — company (masked as needed), as_of / base period, currency/units, forecast
   horizon, and the base / upside / downside final-year revenue, EBITDA, net income, and
   ending cash.
2. **Statements** — per forecast year: the income statement, balance sheet, and cash-flow
   statement, linked and tied.
3. **Schedules** — debt (opening, repayment, closing, interest), PP&E (opening, capex,
   depreciation, closing), and working capital (AR, inventory, AP, net working capital).
4. **Assumptions** — every driver with its `value` and `source`.
5. **Model checks** — balance-sheet identity, cash tie, equity and PP&E roll-forwards, and
   scenario monotonicity.
6. **Machine-readable** — the full model JSON with `model_id`, `inputs_hash`, and
   `config_version` for downstream skills.
7. **Standing disclaimer** — "Model output for analytical support only; not investment advice
   or a recommendation to buy, sell, or hold any security."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. An operating model frequently embeds material non-public
information (management guidance, deal assumptions) — treat the model, inputs, and `model_id`
as need-to-know and respect information barriers / wall-crossing. Retain the model, its
assumptions, and `config_version` per records policy; log the read and any external-delivery
approval. Never exfiltrate MNPI.

## Gotchas
- **A model is not a valuation and not a recommendation.** A forecast is conditional on the
  stated assumptions; it is never a buy/sell/hold, a target, or a value per share.
- **The balance sheet balances by construction — only if the base year does.** A base that
  does not tie is surfaced and carried, not plugged; fix the base before trusting the forecast.
- **Cash is the plug.** Do not "drive" cash directly; it is the cash-flow reconciliation, and
  the cash tie proves the three statements are linked.
- **Opening vs. closing balances.** Interest is on opening debt and depreciation on opening
  net PP&E — this keeps the model non-circular and reproducible; do not switch to closing.
- **Garbage-in dominates.** Small changes in growth, margin, or working-capital days move the
  forecast materially — that is why every driver is sourced and scenarios bracket the base.
- **Do not tune to a number.** Formulas, tolerance, and scenario deltas come from versioned
  config; never bend them to reach a wanted output.
