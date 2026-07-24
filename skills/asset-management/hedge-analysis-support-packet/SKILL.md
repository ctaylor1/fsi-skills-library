---
name: hedge-analysis-support-packet
description: >-
  Calculate exposures, sensitivities, coverage, and scenario P&L for a portfolio-risk
  analyst's human-defined set of candidate hedges, using approved sensitivity models and
  supplied assumptions, and lay them out in a neutral comparison table with an explicit
  limitations list. Use when a portfolio-risk analyst asks to "compare these candidate
  hedges", "work out the residual rate / equity / credit / FX exposure after each overlay",
  "show hedge coverage and scenario P&L", or "reconcile the hedged book to the approved risk
  engine". Produces a reproducible packet (packet_id, inputs_hash) with formula tie-outs,
  provenance on every assumption, and reconciliation to approved-engine totals. HARD
  BOUNDARY: it NEVER selects, recommends, ranks, or endorses a hedge, NEVER decides whether
  or how much to hedge, NEVER executes or stages a trade, and gives no personalized
  investment advice or efficacy guarantee — hedge selection is a portfolio-manager /
  investment-committee decision and execution belongs to the trading desk.
license: MIT
compatibility: Amazon Quick Desktop; requires approved risk-engine (sensitivities/scenarios), model-registry, portfolio-exposure, approved-scenario-library, and versioned hedge-analysis config MCP integrations (all read-only).
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

# Hedge Analysis Support Packet

## Purpose and outcome
Given a portfolio's approved factor sensitivities and a **human-defined set of candidate
hedges**, compute — deterministically and first-order — the **residual exposure per risk
factor**, a **gross-exposure coverage ratio**, the **supplied cost**, and the **scenario P&L**
for the un-hedged portfolio, each hedge alone, and each hedged portfolio, and lay the
candidates out in a **neutral comparison table** with an explicit **limitations** list. Every
figure ties out; every assumption is sourced; the portfolio gross sensitivity and scenario
P&L **reconcile to the approved risk engine**; the packet is reproducible (`packet_id`,
`inputs_hash`) and carries a durable `case_id`. A successful output lets a portfolio-risk
analyst hand the portfolio manager / investment committee a defensible, comparable view of
what each candidate hedge does — while **the hedge decision and the trade stay with humans.**

## Use when
- "Compare these candidate hedges for the book and show the residual exposure and coverage."
- "After each overlay, what's left of our rate / equity / credit / FX sensitivity?"
- "Show the scenario P&L for the portfolio, each hedge, and the hedged book under these shocks."
- "Reconcile the hedged analysis to the approved risk-engine totals and show the tie-outs."
- A portfolio-risk analyst needs a reproducible, source-linked comparison to support (not
  make) a hedging discussion.

## Do not use
- The user wants you to **pick / recommend / rank the best hedge, decide whether or how much
  to hedge, or execute a trade** ("which hedge should we put on?", "execute it") → out of
  scope; produce the comparison and route the decision to the portfolio manager /
  investment committee and execution to the trading desk (see
  [references/handoffs.md](references/handoffs.md)).
- **Personalized investment, legal, or tax advice**, or an **efficacy guarantee** →
  prohibited.
- The base **portfolio exposures** are not yet analyzed → `portfolio-exposure-analyzer`.
- You need the hedge instrument's **prices / Greeks** derived from a pricing model →
  `pricing-hedging-scenario-calculator`.
- **Full multi-factor / historical stress runs** with driver attribution →
  `portfolio-stress-test-runner`; scenario **design** → `stress-test-scenario-designer`.
- **Marginal / total risk-contribution decomposition** → `portfolio-risk-contribution-packet`.
- **Limit / mandate breach testing** of the residual → `market-risk-limit-monitor` /
  `mandate-compliance-monitor`; **transaction-cost** estimation → `transaction-cost-estimator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills supply the base
exposures, the priced hedge sensitivities, and the approved scenarios; this skill emits a
tied-out comparison packet with a durable `case_id`, `packet_id`, `inputs_hash`,
`config_version`, and `model.version`; downstream/parallel review, limit, memo, and execution
steps consume it without recomputing it. It must not duplicate their pricing, stress,
risk-contribution, limit-testing, selection, delivery, or execution work.

## Inputs and prerequisites
- **case_id**, **as_of**, **valuation_date**, **config_version**, reporting **units** and
  **base_currency**.
- **model** — the approved sensitivity model `{id, version, effective_date, provenance,
  citation}`.
- **risk_factors** — each factor's standardized shock **unit** (e.g. `+1bp`, `+1pct`) with
  provenance/citation.
- **portfolio** — `id`, per-factor **sensitivities** `{value, provenance, citation}`, and
  optional **approved_engine_totals** (gross sensitivity + per-scenario P&L) to reconcile to.
- **candidate_hedges** — a non-empty, human-defined list; each `{id, label, sensitivities,
  cost}` with provenance/citation. The skill does **not** invent hedges.
- **scenarios** — each `{id, label, shocks}` in standardized factor units, with
  provenance/citation.
- Read access to the risk engine, model registry, exposure set, scenario library, and
  versioned config (see [references/source-map.md](references/source-map.md)). Full schema:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The portfolio's approved
sensitivities and the approved-engine totals are the anchor; the model registry fixes the
methodology version; hedge specs and the scenario library supply candidate and shock inputs;
versioned config supplies factor units and tolerances. **Cite every assumption with a date;**
a supplied hedge sensitivity or cost is tabulated, never re-derived or priced here; conflicts
are recorded, not silently resolved.

## Workflow
1. **Scope** — confirm portfolio, valuation date, reporting units, factor set, the candidate
   hedge list, and the scenario set; load the approved sensitivities and model version.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors (undefined factors, non-numeric values, missing model version, duplicate hedge ids,
   empty hedge list), note warnings (missing provenance, a hedge that adds exposure, no
   approved totals).
3. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): residual exposure
   per factor and per hedge, gross and per-factor coverage, scenario P&L for portfolio / hedge
   / hedged book, and reconciliation to approved-engine totals.
4. **Read the checks** — confirm every residual, gross, coverage, and scenario tie-out passes,
   the reconciliation holds, every assumption has provenance + citation, and `packet_id` +
   `inputs_hash` are set.
5. **Write the packet** — a plain-language, **neutral** narrative of the exposures and what
   each candidate hedge does to them (residual, coverage, cost, scenario P&L), the comparison
   table, the limitations list, and the standing disclaimer. **No pick, ranking,
   recommendation, or execution.**

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check independently re-derives every tie-out from the packet's own stated
sensitivities and shocks (residual = portfolio + hedge; residual_gross; coverage; scenario
P&L and its linearity identity), re-checks reconciliation to approved-engine totals, requires
provenance + citation on every assumption and `model.id/version/effective_date`, requires
`packet_id` + `inputs_hash`, screens the narrative and limitations for
selection/recommendation/execution/advice/guaranteed-efficacy language, and requires the
disclaimer. **Fail closed on any miss.**

## Human approval
`external-delivery`: human review and approval are required before the packet is delivered to
a portfolio manager, investment committee, trade ticket, OMS, or risk system of record. No
approval is needed for the analyst's own read. The skill takes **no action**, makes **no
hedge decision**, and executes **no trade**.

## Failure handling
- **Missing/non-numeric sensitivity, undefined factor, or empty hedge list** →
  `validate_input` errors; do not guess or invent.
- **Missing model version / effective date** → error; the methodology must be pinned.
- **Unsourced assumption** → warned on input, **rejected** on output.
- **Reconciliation break** (computed ≠ approved-engine beyond tolerance) → fail closed; do
  not present the packet as tied out; surface the break for a human.
- **Hedge adds exposure** (touches a factor the portfolio lacks) → documented result, not an
  error; surface it plainly.
- **Duplicate hedge id / conflicting sources** → stop and surface; keep the sourced anchor.
- **Tool timeout** → return the hedges computed so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — portfolio (masked as needed), `case_id`, valuation date, currency/units,
   model id/version, portfolio gross sensitivity, and the count of candidate hedges compared.
2. **Comparison table** — per candidate hedge: residual exposure by factor, `residual_gross`,
   `coverage_overall` and per-factor coverage, supplied `cost`, and scenario P&L (portfolio /
   hedge / hedged) for each scenario.
3. **Assumptions register** — every model, factor unit, portfolio sensitivity, hedge
   sensitivity, cost, and scenario shock with `provenance` + `citation`.
4. **Model checks** — the tie-out results and the reconciliation to approved-engine totals.
5. **Limitations** — first-order-only, basis risk, cost/liquidity/counterparty exclusions,
   and that hedge selection is out of scope.
6. **Machine-readable** — the full packet JSON with `packet_id`, `inputs_hash`,
   `config_version`, and `model.version` for downstream skills.
7. **Standing disclaimer** — "Illustrative hedge-analysis support packet for analytical
   purposes only. It calculates exposures, sensitivities, coverage, and scenario P&L for a
   human-defined set of candidate hedges under supplied, approved-model assumptions; it does
   not select, recommend, rank, or endorse any hedge, is not a recommendation to enter,
   adjust, or unwind any position, is not investment, legal, or tax advice, and does not
   authorize or execute any trade. Hedge selection and execution are human decisions; results
   are only as good as the stated assumptions, which a qualified human must review."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. Portfolio sensitivities and candidate hedges reveal positioning
and forward intent — treat the packet, its inputs, `case_id`, and `packet_id` as need-to-know
and respect information barriers. Retain the packet, its assumptions register,
`config_version`, and `model.version` per records policy; log the read and any
external-delivery approval. Never exfiltrate position or hedge-intent data.

## Gotchas
- **A comparison is not a choice.** Presenting residual, coverage, cost, and scenario P&L
  side by side is analysis; naming a "best" hedge, ranking them to a winner, or nudging a pick
  crosses the R2 boundary.
- **Coverage measures offset, not value.** A high coverage ratio says nothing about cost,
  liquidity, basis risk, counterparty/collateral impact, or tracking error.
- **First-order only.** Linear sensitivities miss convexity/gamma and non-linear payoffs; a
  put modeled as a delta proxy understates its behaviour in a large move — flag it.
- **A hedge on a factor you don't hold adds risk.** Residual = the hedge's own sensitivity;
  this is surfaced, not an error.
- **Reconcile or stop.** If the portfolio gross or a scenario P&L does not tie to the
  approved engine, the packet is not "tied out" — do not present it as such.
- **Units must match.** Sensitivities and shocks are both in each factor's standardized unit;
  mixing bp with % silently corrupts every number.
- **Do not tune to a number.** Factor units, tolerances, and shocks come from versioned
  config and the approved model; never bend them to reach a wanted coverage or P&L.
