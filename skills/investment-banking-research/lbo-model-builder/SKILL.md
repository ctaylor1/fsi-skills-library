---
name: lbo-model-builder
description: >-
  Build a source-linked leveraged-buyout model: entry Sources & Uses with a sponsor-equity
  plug, a per-tranche debt schedule with beginning-balance interest, mandatory amortization
  and a cash sweep, a levered free-cash-flow forecast with liquidity, an exit at an
  EV/EBITDA multiple, and MOIC / IRR across base, upside, and downside cases — with formula
  tie-outs, assumption provenance, and reproducibility. Use when a financial-sponsors or
  leveraged-finance analyst asks to "build an LBO", "model the debt schedule and cash
  sweep", "run entry and exit at a multiple", or "show the sponsor returns (MOIC/IRR)". This
  skill models and explains only; it NEVER issues an investment recommendation
  (invest/pass/commit), NEVER guarantees a return, IRR, or exit value, NEVER approves a deal
  or renders an investment-committee decision or fairness opinion, and NEVER gives
  personalized investment, legal, or tax advice — those are licensed-human /
  investment-committee judgments.
license: MIT
compatibility: Amazon Quick Desktop; requires filing-intelligence, market/financial-data, approved operating-model, research-corpus, data-room, and approved-calculation MCP integrations, plus versioned LBO config (all read-only).
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
  aws-fsi-primary-user: "Financial-sponsors / leveraged-finance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# LBO Model Builder

## Purpose and outcome
Given a target's entry EBITDA, a purchase multiple, a proposed capital structure, and an
explicit set of operating drivers, build a **deterministic, source-linked LBO**: balance
entry Sources & Uses with a sponsor-equity plug, roll a per-tranche debt schedule with
beginning-balance interest, mandatory amortization, and a cash sweep, project levered free
cash flow and liquidity, exit at an EV/EBITDA multiple, and walk down to sponsor exit equity,
MOIC, and IRR — across **base / upside / downside** cases, every figure tied out and every
assumption sourced. A successful output lets an analyst defend each number to a reviewer,
deal team, or investment committee, and hands a reproducible model (`model_id`) to downstream
memo, pitch, and review skills. The **investment judgment stays with a licensed human.**

## Use when
- "Build an LBO for this target / model this buyout."
- "Set up Sources & Uses and solve for the sponsor equity."
- "Model the debt schedule, mandatory amortization, and cash sweep."
- "Run entry at 10x and exit at 10x and show me the returns (MOIC / IRR)."
- "Give me base, upside, and downside LBO cases with the tie-outs and assumption sources."
- An analyst needs a defensible, reproducible model to anchor a returns / financing section.

## Do not use
- The user wants an **investment recommendation, a guaranteed return, a deal approval, or a
  fairness opinion** ("should we do this deal?", "is the IRR guaranteed?") → out of scope;
  build the model and route the judgment to the deal team / investment committee (see
  [references/handoffs.md](references/handoffs.md)).
- **Personalized investment, legal, or tax advice** → licensed-human matter.
- The upstream **operating model** does not exist yet → `three-statement-model-builder`.
- **Entry/exit multiple or leverage benchmarking** (trading comps / precedents) →
  `comps-analysis-builder`.
- Full **sensitivity/tornado grids** beyond the three cases → `scenario-sensitivity-generator`.
- **Intrinsic** (unlevered DCF) or **strategic-acquisition** valuation → `dcf-modeler` or
  `merger-model-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills supply the operating
drivers and base-year financials; this skill emits a tied-out model with a durable
`model_id`, `inputs_hash`, and `config_version`; downstream review/memo/pitch skills consume
it without rebuilding it. It must not duplicate their recommendation, delivery, or review
steps.

## Inputs and prerequisites
- **Company identifier** and an **entry date** (anchors the entry multiple, LTM EBITDA, and
  debt pricing).
- **Entry EBITDA** and **entry multiple** (purchase price), **hold years**, and **fees**
  (transaction %, financing %), each as `{value, provenance, citation}`.
- **Debt tranches** — for each: `name`, `turns` (× entry EBITDA), `rate`, `amort_pct`, and a
  `cash_sweep` flag.
- **Operating drivers** — base revenue, revenue growth, EBITDA margin, D&A %, capex %,
  working-capital % of revenue change, tax rate, and cash-sweep % — each sourced.
- **Liquidity** (opening cash, minimum-cash floor), **exit multiple**, and
  **scenario_adjustments** for upside/downside. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to filing-intelligence, market data, the approved operating model, the data
  room, and the versioned LBO config (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filed financials are the anchor for
LTM EBITDA and historicals; the sponsor/management model supplies operating drivers; market
data supplies debt pricing, leverage, and multiples; the data room supplies credit terms;
research gives sanity ranges; versioned config supplies scenario deltas and conventions. A
model input is only as good as its source — **cite every assumption with a date**; a filed
number outranks an estimate, and conflicts are recorded as explicit sourced overrides.

## Workflow
1. **Scope** — confirm company, entry date, currency/units, hold horizon, capital structure,
   and exit method; load LTM EBITDA, operating drivers, and financing terms.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors, note warnings (missing provenance, entry-EBITDA vs revenue×margin mismatch,
   out-of-range terms, high leverage, long hold).
3. **Build the model (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): balance Sources &
   Uses, roll the debt schedule with interest / amortization / cash sweep, project levered
   FCF and liquidity, exit at the multiple, and produce base / upside / downside returns with
   per-scenario tie-outs.
4. **Read the checks** — confirm Sources & Uses balance, every roll-forward and returns
   tie-out passes, scenarios are monotonic, and liquidity holds; every assumption is in the
   register with provenance + citation.
5. **Write the pack** — a plain-language narrative of the entry, capital structure, debt
   paydown, exit, and the returns range across cases, with explicit assumptions and their
   sources — and the standing disclaimer. No recommendation, guarantee, or approval.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check independently re-derives every tie-out (Sources & Uses balance;
per-tranche interest on beginning balance; the levered-FCF build; the debt and cash
roll-forwards; the exit walk; and MOIC / IRR), confirms scenario monotonicity, requires
provenance + citation on every assumption and `model_id` + `inputs_hash`, screens the
narrative for advice / recommendation / return-guarantee / approval language, and requires
the disclaimer. **Fail closed on any miss.**

## Human approval
`external-delivery`: human review and approval are required before the model is delivered to
a client, deal team, investment committee, data room, or CRM, or written to any system of
record. No approval is needed for the analyst's own read. The skill takes **no action** and
makes **no investment decision**.

## Failure handling
- **Missing/non-numeric driver or entry term** → `validate_input` errors; do not guess.
- **Unsourced assumption** → warned on input, **rejected** on output; every number needs a
  source.
- **Unbalanced Sources & Uses / debt schedule that does not roll forward** → formula
  failure; fail closed, do not present it as valid.
- **Liquidity shortfall** (`min_cash_ok = false`) → surface the year(s) where free cash flow
  cannot cover interest and amortization; do not run cash silently negative.
- **Non-monotonic scenarios** → the scenario deltas or drivers are inconsistent; stop and
  surface it rather than shipping an incoherent returns range.
- **Conflicting sources** → keep the filed anchor, record the estimate as a sourced
  override, cite both.
- **Tool timeout** → return the scenarios computed so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — company (masked as needed), entry date, currency/units, entry multiple and
   leverage, and the base / upside / downside MOIC and IRR range.
2. **Sources & Uses** — purchase EV, fees, new-debt tranches, sponsor-equity plug, and the
   sources = uses balance.
3. **Model** — per scenario: the operating forecast (revenue → EBITDA → EBIT), the debt
   schedule (beginning, interest, amortization, sweep, ending) per tranche, the levered-FCF
   build, cash and net debt, the exit walk, and MOIC / IRR.
4. **Assumptions register** — every entry term, capital-structure term, operating driver,
   exit input, and liquidity input with `provenance` + `citation`.
5. **Model checks** — the Sources & Uses balance, the tie-out results, scenario
   monotonicity, and the minimum-cash / liquidity flag.
6. **Machine-readable** — the full model JSON with `model_id`, `inputs_hash`, and
   `config_version` for downstream skills.
7. **Standing disclaimer** — "Illustrative leveraged-buyout model for analytical purposes
   only; not investment advice, not a recommendation to make, hold, or exit any investment,
   not a guarantee of any return, IRR, or multiple, and not an investment-committee approval.
   Outputs depend entirely on the stated assumptions, which a qualified human must review."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. An LBO model embeds material non-public information (management
projections, deal price, financing terms) — treat the model, inputs, and `model_id` as
need-to-know and respect information barriers / wall-crossing. Retain the model, its
assumptions register, and `config_version` per records policy; log the read and any
external-delivery approval. Never exfiltrate MNPI.

## Gotchas
- **Returns are not a recommendation.** A MOIC / IRR is conditional on the stated
  assumptions; it is never an invest/pass decision, a guarantee, or a committee approval.
- **Leverage dominates returns.** Small changes in entry multiple, leverage, or exit
  multiple move IRR enormously — that is why every assumption is sourced and cases bracket
  the base. Multiple expansion is a choice, not a given; state it.
- **Interest is on the beginning balance** by convention, so the model stays iteration-free;
  a mid-period or average-balance convention would shift interest and returns.
- **Sources must equal uses.** Sponsor equity is the plug; an unbalanced S&U is a formula
  error, never a modelling preference.
- **Watch liquidity.** A high sweep and thin minimum cash can starve the business in a
  downside; the model flags it rather than hiding a negative cash balance.
- **Single entry-to-exit cash flow.** The base IRR assumes no interim distributions; dividend
  recaps change the return profile and are out of scope for the base engine.
- **Do not tune to a number.** Formulas, tolerance, fees, and scenario deltas come from
  versioned config; never bend them to reach a wanted return.
