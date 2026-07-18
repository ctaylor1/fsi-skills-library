---
name: merger-model-builder
description: >-
  Build a deterministic, source-linked merger model — accretion/(dilution) and pro forma
  ownership — from explicit driver assumptions covering consideration and offer premium,
  financing mix (new debt, cash on hand, new equity), run-rate synergies, purchase-accounting
  write-ups, and financing fees, with base/upside/downside scenarios and a sensitivity grid.
  Use when an M&A or corporate-development analyst asks "is this deal accretive or dilutive",
  "build an accretion/dilution model", "what's the pro forma EPS / ownership split", "how much
  synergy to break even", or wants a reproducible pro forma deliverable for review. HARD
  BOUNDARY: illustrative model of stated assumptions only — it NEVER gives investment advice,
  a buy/sell/hold view, a price target, a valuation or fairness opinion, or a recommendation
  to transact, and every figure requires human analyst review before external delivery.
license: MIT
compatibility: Amazon Quick Desktop; requires market/financial-data, filings, research-corpus, deterministic-calculation, and spreadsheet/presentation MCP integrations (all read-only), plus CRM/data-room read access.
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
  aws-fsi-primary-user: "M&A analyst / corporate-development analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Merger Model Builder

## Purpose and outcome
Given standalone financials for an acquirer and a target plus a set of deal drivers, build a
**deterministic pro forma model** that computes EPS **accretion/(dilution)**, the **pro forma
ownership split**, the **breakeven synergies**, a **base/upside/downside scenario set**, and a
**two-driver sensitivity grid** — each figure tied to the assumption that produced it. A
successful output is a reproducible, auditable model an analyst can review, drop into a
committee memo or pitch, and defend line by line. Every number is a mechanical consequence of
the stated drivers; the judgment about whether to pursue the deal stays with the human.

## Use when
- "Is this acquisition accretive or dilutive to EPS?"
- "Build an accretion/dilution model at a 20% premium, 50/50 cash and stock."
- "What's the pro forma EPS and the ownership split if we issue stock to fund half of it?"
- "How much run-rate synergy do we need for the deal to break even on EPS?"
- "Show base/upside/downside and a premium-vs-synergy sensitivity table."
- An analyst needs a consistent, source-linked pro forma deliverable for review.

## Do not use
- The user wants a **recommendation, buy/sell/hold view, price target, valuation opinion, or
  fairness opinion** ("should we do this deal?", "what's it worth?", "is the price fair?") →
  out of scope. Provide the mechanical model and route the judgment to the deal team and a
  licensed valuation/fairness specialist.
- **Intrinsic / standalone valuation** (DCF, WACC, terminal value) → `dcf-modeler`.
- **Trading or transaction comparables** for a valuation range → `comps-analysis-builder`.
- A **standalone three-statement forecast** for either company (the inputs to this model) →
  `three-statement-model-builder`.
- A **financial-sponsor / leveraged buyout** returns model (IRR, MOIC, debt schedule) →
  `lbo-model-builder`.
- Broader **scenario/sensitivity** design beyond this model's grid →
  `scenario-sensitivity-generator`.
- Packaging the result into a **pitch** or **diligence pack** →
  `investment-banking-pitch-builder` or `due-diligence-packager`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill consumes standalone
projections and valuation inputs from upstream skills and emits a model with a durable
`model_id`; downstream pitch/diligence/scenario skills consume that `model_id` rather than
rebuilding the pro forma. It never issues a valuation or fairness opinion — that is a licensed
human specialist's role.

## Inputs and prerequisites
- **Acquirer and target standalone financials**: net income, diluted shares, share price
  (plus tax rate), each with a `source_ref` to the filing or model of record.
- **Deal drivers**: offer price per share **or** premium, cash/stock consideration mix,
  financing plan (cash on hand used, new-debt rate, foregone cash yield, financing fees and
  amortization), run-rate pre-tax synergies and phasing, purchase-accounting intangible
  write-up and amortization, transaction fees, and the pro forma tax rate.
- Optional **scenario drivers** (synergy realization and premium multiplier per case) and the
  **assumptions version** so a run is reproducible.
- Schema and integrity rules: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filed financials are the position of
record for standalone figures; the deal team's approved offer terms and financing plan govern
deal drivers; the versioned assumptions pack governs tax and default scenario drivers. Cite
every driver to its source; where a driver is a management estimate (synergies, write-ups),
label it as an estimate, not a fact.

## Workflow
1. **Scope & confirm** — identify acquirer, target, and the deal structure; gather standalone
   financials and deal drivers; record the `assumptions_version`.
2. **Validate input (deterministic)** — run `validate_input`; fail closed on structural or
   arithmetic-integrity errors (bad shares/price, consideration mix that does not sum to
   100%, missing offer basis). Resolve warnings (thin provenance, missing synergies) or state
   their effect.
3. **Build the model (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute
   consideration, financing, after-tax adjustments, standalone vs pro forma EPS,
   accretion/(dilution), ownership split, breakeven synergies, scenarios, and the sensitivity
   grid. See [references/domain-rules.md](references/domain-rules.md) for every formula.
4. **Tie out & review** — run [scripts/validate_output.py](scripts/validate_output.py); it
   independently recomputes the reported figures, confirms scenario monotonicity and
   provenance, and screens for advice language. Correct any failure and re-run.
5. **Assemble the deliverable** — output table + scenario/sensitivity views + explicit
   assumptions with citations + the standing disclaimer, ready for analyst review.

## Validation loop
Run `validate_input` before and `validate_output` after. The output check confirms: every
formula ties out on an independent recompute (consideration, shares, EPS, accretion,
ownership); every driver assumption carries a citation and the required drivers are present;
scenarios are monotonic (more synergy / lower premium is never less accretive); the `model_id`
stamps the assumptions version; and **no investment-advice, price-target, or fairness-opinion
language** is present, with the standing disclaimer intact. Fail closed on any miss.

## Human approval
`external-delivery`: human analyst review is required before the model is delivered to a
client, committee, or system of record. No approval is needed for the analyst's own internal
draft. The skill never commits the model to a system of record and never authorizes a
transaction.

## Failure handling
- **Thin baseline / missing drivers** → compute only what the data supports; mark defaulted
  drivers explicitly; do not fabricate synergies or write-ups.
- **Consideration mix does not sum to 100%** → fail closed; the split must be well-formed.
- **Ambiguous entity/period** → stop and confirm; never mix an acquirer's FY with a target's
  stub period silently.
- **Cash on hand exceeds cash consideration** → new debt floors at 0 and the model warns; do
  not create negative debt.
- **Stale/conflicting sources** → cite both and flag; do not silently pick one.
- **Tool timeout** → return the base case computed so far with an "incomplete" flag; scenarios
  and sensitivity are resumable.

## Output contract
1. **Summary** — deal id, as-of, base-case verdict (accretive/dilutive/neutral) and
   accretion/(dilution) %, standalone vs pro forma EPS, pro forma ownership split.
2. **Consideration & financing** — offer value, cash/stock split, new shares issued, new debt,
   cash used.
3. **Adjustments** — after-tax synergies, incremental interest, foregone interest, write-up
   amortization, financing-fee amortization.
4. **Scenarios** — base/upside/downside accretion and pro forma EPS.
5. **Sensitivity** — premium multiplier x synergy realization grid of accretion %.
6. **Breakeven synergies** — pre-tax run-rate synergies for EPS neutrality.
7. **Assumptions & provenance** — every driver with value and citation.
8. **Machine-readable** — the full model JSON with `model_id` for downstream skills.
9. **Standing disclaimer** — "Illustrative pro forma model based on stated assumptions; not
   investment advice, a fairness opinion, or a recommendation to transact."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Treat deal identity, targets, and terms as highly confidential;
use code names where available and minimize identifying data in the output. Retain the model,
its inputs, and the `assumptions_version` so a run is reproducible; log the read and any
external-delivery approval. Never exfiltrate deal data or place it in unapproved channels.

## Gotchas
- **A model is not a recommendation.** Accretion is a mechanical result of the drivers, never
  a view on whether to do the deal or buy the stock — that boundary is enforced in
  `validate_output`.
- **Synergies and write-ups are estimates**, not facts; label them and let the scenario range
  carry the uncertainty. Do not tune drivers to force a desired verdict.
- **Tax-effect adjustments consistently**: synergies, incremental interest, foregone interest,
  and financing-fee amortization are tax-effected; intangible amortization is tax-effected
  only when deductible (see `amort_tax_deductible`).
- **Transaction fees are one-time** and are excluded from run-rate EPS; they affect
  goodwill/equity, not the recurring accretion figure — state this so it is not double-counted.
- **Exclude the target's own share count from pro forma shares**; pro forma shares are the
  acquirer's shares plus **new** shares issued for the stock consideration only.
- **Premium vs offer price**: give one basis, not both in conflict; the model derives the
  other and records the premium in the assumptions.
