---
name: dcf-modeler
description: >-
  Build a source-linked discounted-cash-flow valuation: an explicit driver-based unlevered
  free-cash-flow forecast, a WACC derived from its stated components, a terminal value
  (Gordon growth or exit multiple), an enterprise-to-equity bridge to value per share, and
  base / upside / downside scenarios with full formula tie-outs and reproducibility. Use
  when an investment-banking or research analyst asks to "build a DCF", "value this company
  by DCF", "model WACC and terminal value", "walk enterprise value to equity", or wants a
  scenario DCF with drivers, sensitivities, and model checks. This skill models and explains
  only; it NEVER issues an investment recommendation (buy/sell/hold), a price target, a
  fair-value verdict presented as a decision, or a fairness opinion, NEVER guarantees a
  return or future price, and NEVER gives personalized investment, legal, or tax advice —
  those are licensed-human / investment-committee judgments.
license: MIT
compatibility: Amazon Quick Desktop; requires filing-intelligence, market/financial-data, approved operating-model, research-corpus, and approved-calculation MCP integrations, plus versioned valuation config (all read-only).
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

# DCF Modeler

## Purpose and outcome
Given a company's base-year financials and an explicit set of forecast drivers, build a
**deterministic, source-linked DCF**: project unlevered free cash flow, discount it at a
WACC derived from its stated components, add a terminal value, walk enterprise value down an
explicit bridge to equity value and value per share, and produce **base / upside / downside**
scenarios — every figure tied out and every assumption sourced. A successful output lets an
analyst defend each number to a reviewer, deal team, or investment committee, and hands a
reproducible model (`model_id`) to downstream memo, pitch, and review skills. The
**valuation judgment stays with a licensed human.**

## Use when
- "Build a DCF for this company / value it by discounted cash flow."
- "Model the WACC, terminal value, and enterprise-to-equity bridge."
- "Give me base, upside, and downside DCF scenarios with the tie-outs."
- "Show the driver assumptions and where each one comes from."
- An analyst needs a defensible, reproducible model to anchor a valuation section.

## Do not use
- The user wants a **recommendation, price target, fair-value verdict as a decision, or
  fairness opinion** ("should I buy?", "what's your target?") → out of scope; build the
  model and route the judgment to a licensed analyst / investment committee (see
  [references/handoffs.md](references/handoffs.md)).
- **Personalized investment, legal, or tax advice** → licensed-human matter.
- The upstream **operating model** does not exist yet → `three-statement-model-builder`.
- **Relative valuation** (trading comps / precedents) → `comps-analysis-builder`.
- Full **sensitivity/tornado grids** beyond the three cases → `scenario-sensitivity-generator`.
- **Return-based / transaction** valuation → `lbo-model-builder` or `merger-model-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills supply the drivers and
base-year financials; this skill emits a tied-out model with a durable `model_id`,
`inputs_hash`, and `config_version`; downstream review/memo/pitch skills consume it without
rebuilding it. It must not duplicate their recommendation, delivery, or review steps.

## Inputs and prerequisites
- **Company identifier** and a **valuation date** (anchors WACC market inputs and share count).
- **Base-year revenue**, **shares outstanding**, and **bridge items** (debt, cash, minority
  interest, preferred, associates) from filed financials.
- **Forecast drivers** — revenue growth, EBIT margin, tax rate, D&A %, capex %, and working-
  capital % of revenue change — each as `{value, provenance, citation}`.
- **WACC components** (risk-free, ERP, beta, pre-tax cost of debt, capital weights) or an
  explicit `wacc.override`; **terminal** method + input (growth or exit multiple);
  **scenario_adjustments** for upside/downside. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to filing-intelligence, market data, the approved operating model, and the
  versioned valuation config (see [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filed financials are the anchor;
management guidance and market data supply forward and rate inputs; research/consensus gives
sanity ranges; versioned config supplies scenario deltas and conventions. A forecast driver
is only as good as its source — **cite every assumption with a date**; a filed number
outranks an estimate, and conflicts are recorded as explicit sourced overrides.

## Workflow
1. **Scope** — confirm company, valuation date, currency/units, forecast horizon, terminal
   method, and discounting convention; load base-year financials and drivers.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors, note warnings (missing provenance, WACC not > g, weights ≠ 1, long horizon).
3. **Build the model (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): compute WACC from
   components, project UFCF per year, discount, add the terminal value, walk the enterprise-
   to-equity bridge, and produce base / upside / downside with per-scenario tie-outs.
4. **Read the checks** — confirm every tie-out passes, scenarios are monotonic, and the
   Gordon guard holds; every assumption is in the register with provenance + citation.
5. **Write the pack** — a plain-language narrative of drivers, WACC, terminal value, the
   bridge, and the scenario range, with explicit assumptions and their sources — and the
   standing disclaimer. No recommendation, target, or opinion.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check independently re-derives the tie-outs (EV = ΣPV + PV(TV); per-year
PV; non-increasing discount factors; bridge and per-share), confirms scenario monotonicity
and the Gordon guard, requires provenance + citation on every assumption and `model_id` +
`inputs_hash`, screens the narrative for advice/recommendation/target/opinion language, and
requires the disclaimer. **Fail closed on any miss.**

## Human approval
`external-delivery`: human review and approval are required before the model is delivered to
a client, deal team, data room, or CRM, or written to any system of record. No approval is
needed for the analyst's own read. The skill takes **no action** and makes **no valuation
decision**.

## Failure handling
- **Missing/non-numeric driver** → `validate_input` errors; do not guess a driver.
- **Unsourced assumption** → warned on input, **rejected** on output; every number needs a
  source.
- **WACC ≤ terminal growth (Gordon)** → invalid terminal value; fail closed, do not present
  it as valid (offer the exit-multiple method or a revised WACC/g).
- **Non-monotonic scenarios** → the scenario deltas or drivers are inconsistent; stop and
  surface it rather than shipping an incoherent range.
- **Conflicting sources** → keep the filed anchor, record the estimate as a sourced
  override, cite both.
- **Tool timeout** → return the scenarios computed so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — company (masked as needed), valuation date, currency/units, WACC, terminal
   method, and the base / upside / downside value-per-share range.
2. **Model** — per scenario: the UFCF forecast (revenue → EBIT → NOPAT → +D&A −capex −ΔNWC),
   discount factors and PVs, terminal value, enterprise value, the enterprise-to-equity
   bridge, equity value, and value per share.
3. **Assumptions register** — every driver, WACC component, terminal input, and bridge item
   with `provenance` + `citation`.
4. **Model checks** — the tie-out results, scenario monotonicity, and the Gordon guard.
5. **Machine-readable** — the full model JSON with `model_id`, `inputs_hash`, and
   `config_version` for downstream skills.
6. **Standing disclaimer** — "Illustrative valuation model for analytical purposes only; not
   investment advice, not a recommendation to buy, sell, or hold any security, not a price
   target, and not a fairness opinion. Outputs depend entirely on the stated assumptions,
   which a qualified human must review."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. A DCF frequently embeds material non-public information
(management guidance, deal assumptions) — treat the model, inputs, and `model_id` as
need-to-know and respect information barriers / wall-crossing. Retain the model, its
assumptions register, and `config_version` per records policy; log the read and any
external-delivery approval. Never exfiltrate MNPI.

## Gotchas
- **A valuation is not a recommendation.** A value per share is conditional on the stated
  assumptions; it is never a buy/sell/hold, a target, or a fairness opinion.
- **Garbage-in dominates.** Small changes in growth, margin, WACC, or terminal g move the
  value enormously — that is why every assumption is sourced and scenarios bracket the base.
- **Gordon requires WACC > g**, and the terminal value usually dominates enterprise value;
  a small g change is not "small". Sanity-check the terminal-value share of EV.
- **Mid-year vs end-year** convention materially shifts value; state which you used.
- **Do not double-count** the bridge: cash added back must not also sit inside net debt;
  the bridge lists debt and cash as separate signed lines to keep it inspectable.
- **Do not tune to a number.** Formulas, tolerance, and scenario deltas come from versioned
  config; never bend them to reach a wanted valuation.
