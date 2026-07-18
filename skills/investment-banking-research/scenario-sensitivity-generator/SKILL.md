---
name: scenario-sensitivity-generator
description: >-
  Build scenario, sensitivity, breakeven, and decision-threshold analyses around the most
  material operating and valuation drivers of a supplied financial model. Use when a banking,
  research, or investment analyst asks to "flex the assumptions", "run bull/bear cases",
  "build a sensitivity table", "what margin breaks even", "how high does the multiple have to
  go", or needs a reproducible driver-by-output data table for a memo, model, or pitch. The
  skill recomputes outputs deterministically from explicit, cited driver assumptions and ties
  every number back to a formula. HARD BOUNDARY: it computes mechanics only — it NEVER issues
  a buy/sell/hold recommendation, a price target presented as advice, or any personalized
  investment/tax advice, and a human must review before external delivery.
license: MIT
compatibility: Amazon Quick Desktop; requires market/financial-data, filings, research-corpus, entity-resolution, deterministic-computation, and controlled-template MCP integrations (all read-only); the bundled scripts are stdlib-only and self-contained.
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
  aws-fsi-primary-user: "Banking / research / investment analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Scenario & Sensitivity Generator

## Purpose and outcome
Given a base-case financial model expressed as **explicit driver assumptions** and
**transparent output formulas**, produce a reproducible analytical pack: named **scenarios**
(e.g. base/bull/bear), one-way and two-way **sensitivity tables**, **breakevens** (the driver
value at which an output hits a target), and **decision thresholds** (the driver level at
which an output crosses a reference level). Every output is recomputed deterministically and
ties back to a formula and a cited driver value. A successful output gives an analyst a
defensible, review-ready exhibit for a memo, model tab, or pitch page — the interpretation,
recommendation, and any decision remain the human's.

## Use when
- "Flex the assumptions / run bull and bear cases on this model."
- "Build a sensitivity table of implied share price to EBITDA margin and multiple."
- "What EBITDA margin makes equity value break even?" / "How high does the multiple have to
  go to reach X?"
- "Show the two-way data table for growth vs. discount rate."
- An analyst needs a consistent, reproducible driver-by-output exhibit tied to stated inputs.

## Do not use
- The user wants a **valuation built from scratch** (DCF, comps, LBO, merger, three-statement
  operating model) → route to `dcf-modeler`, `comps-analysis-builder`, `lbo-model-builder`,
  `merger-model-builder`, or `three-statement-model-builder`; this skill flexes an *existing*
  model, it does not originate the base case.
- The user wants a **recommendation, rating, price target, or "is this a good investment"**
  → out of scope and prohibited. Provide the mechanics and route the judgment to a licensed
  research/deal professional.
- The user wants the analysis **assembled into a deck or memo** → hand the pack to
  `investment-banking-pitch-builder`, `company-profile-builder`, or `due-diligence-packager`.
- **Market sizing / TAM** driver work with no existing model → `market-sizing-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill consumes a base-case model
(with driver provenance) from upstream modeling skills and emits an analysis pack with a
durable `analysis_id`; downstream packaging skills embed the pack. It must not re-originate a
valuation or add a recommendation.

## Inputs and prerequisites
- A **base-case model** as JSON: drivers (name, base value, unit, `source_ref`, and
  `provenance` naming the upstream model/source), and outputs (name + `formula`). Formulas are
  **whitelisted arithmetic only** (`+ - * / ** %`, parentheses, `min`/`max`/`abs`, references
  to drivers and earlier outputs) — no code, no lookups, no learned functions.
- The requested analyses: `scenarios` (driver overrides), `sensitivities` (driver, output,
  points), `two_way` tables, `breakevens` (driver, output, target), `decision_thresholds`
  (driver, output, target, optional bracket).
- A recorded `config_version` for the assumption set (reproducibility) and `as_of` date.
- Schema and field detail: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **upstream model** is the
position of record for base driver values; market/financial data and filings substantiate a
driver only where the model cites them; the assumption/config set is a **versioned contract**.
Every driver carries a `source_ref`; the pack records the `config_version` used so a run is
reproducible. Cite conflicts rather than silently resolving them.

## Workflow
1. **Scope & confirm** — identify the base-case model, the material drivers to flex, and the
   analyses requested. Confirm the `as_of` and `config_version`.
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); fail
   closed on undefined formulas, unknown driver/output references, or missing driver
   provenance.
3. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the base
   case, scenarios, one-way and two-way sensitivities, breakevens (bisection to target), and
   decision thresholds. Each output is recomputed from drivers + formulas; nothing is
   estimated or free-typed.
4. **Assemble the pack** — base case, scenario grid with deltas vs. base, sensitivity tables,
   breakeven/threshold solutions with their brackets, and the assumption provenance.
5. **Write the exhibit** — plain-language description of what each table shows and what drives
   it, the explicit assumptions and their sources, the ranges tested, and the standing
   no-advice disclaimer. Describe behaviour ("value rises with margin"); never prescribe an
   action.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check **independently re-derives** every number from the stated drivers and
formulas and confirms: base-case, scenario, sensitivity, two-way, breakeven, and threshold
values all tie out; every driver has provenance and every output has a formula; a converged
breakeven/threshold plugged back into the model hits its target; `model_id`/`config_version`
are present (reproducibility); and there is **no investment-advice language**, with the
standing disclaimer present. Fix and re-run until it passes; fail closed on any miss.

## Human approval
`external-delivery`: a human must review and approve before the pack is delivered to a client
or written to a system of record (deal file, model repository, published research). Internal
analytical use may be reviewer-sampled. The skill makes no system-of-record change itself and
stages nothing for execution.

## Failure handling
- **Undefined / unsupported formula** or a reference to an unknown driver/output → stop; the
  model definition must be corrected (do not guess a formula).
- **Missing driver provenance** (`source_ref`) → fail closed; assumptions must be traceable.
- **Breakeven/threshold not bracketed** (no sign change in range) → report "no crossing in
  range"; do not extrapolate beyond the tested bracket.
- **Non-monotonic output** over the solve range → the reported root is one crossing; state
  that others may exist and widen/relayer the bracket rather than asserting uniqueness.
- **Stale / conflicting driver sources** → cite both and flag; never silently pick one.
- **Tool timeout / very large grids** → return the analyses completed so far with an
  "incomplete" flag; split large two-way tables into resumable stages.

## Output contract
1. **Summary** — model id, `as_of`, `config_version`, currency/unit, base-case outputs.
2. **Scenarios** — per scenario: overrides applied, each output, and delta / % vs. base.
3. **Sensitivities** — one-way tables (driver value → output, % change) and two-way data
   tables (row driver × col driver → output).
4. **Breakevens & decision thresholds** — the solved driver value, the target, the bracket
   searched, convergence status, and which side the base case sits on (stated factually).
5. **Assumptions & provenance** — every driver, its base value, unit, and `source_ref`.
6. **Machine-readable** — the full analysis JSON + `analysis_id` for downstream packaging.
7. **Standing disclaimer** — "Analytical scenario and sensitivity output only; not investment
   advice, a recommendation, or a price target. Assumptions are user/model-supplied and must
   be reviewed by a qualified professional before any decision or external delivery."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
MNPI / client-confidential. Treat model contents and driver values as material non-public
information: restrict to the deal/coverage team, honor information barriers, and never
co-mingle across walls. Minimize any client identifiers in the output to what the exhibit
needs. Retain the analysis + assumption set + `config_version` per records policy; log the
read and any external-delivery approval. Never exfiltrate model or client data.

## Gotchas
- **A table is not a thesis.** Sensitivities and breakevens describe mechanical behaviour;
  they never imply a recommendation, a fair value, or an action.
- **Garbage-in drivers dominate.** The output is only as good as the base assumptions —
  provenance is required precisely because a plausible-looking table can rest on an unsourced
  guess. Flag thin or stale assumptions.
- **Breakevens can be non-unique.** A monotonic-looking output may cross a target more than
  once; the bisection returns one root in the bracket. State the bracket and monotonicity
  caveat.
- **Two-way tables explode.** Grid size is rows × cols × formula cost; cap ranges and split
  into stages rather than timing out mid-table.
- **Reproducibility is the deliverable.** Pin the `config_version`; the same inputs must
  reproduce the same numbers, or the exhibit cannot be defended in review.
- **No advice, even implicitly.** Phrases like "implies upside", "attractive entry", or a
  standalone "price target" cross the line — the output validator screens for them.
