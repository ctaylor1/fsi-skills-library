---
name: financing-alternatives-calculator
description: >-
  Compute the illustrative cost and impact of documented financing alternatives (e.g. term loan,
  bond, equity) side by side — annual interest, amortized upfront fees, all-in annual cost,
  effective cost rate, total cost over term, and equity dilution — as a factual comparison
  worksheet for a DCM/ECM analyst. Use when an analyst asks to "compare the cost of these
  financing options", "what's the all-in cost of a term loan vs a bond", "model the dilution
  from an equity raise", or "build a financing-alternatives worksheet". HARD BOUNDARY: R2
  model-and-calculate — it presents the numbers for each alternative only; it NEVER recommends,
  ranks, or names a "cheapest/best/optimal" option, and NEVER advises which to choose; the banker
  owns all advice. MNPI/information-barrier controls apply. Routes the debt-stack map to
  capital-structure-maturity-mapper.
license: MIT
compatibility: Amazon Quick Desktop; requires documented financing terms and reference-data MCP integrations (all read-only). Deterministic stdlib-only computation. MNPI-aware.
metadata:
  aws-fsi-category: "Investment Banking & Research"
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
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "DCM/ECM analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Financing Alternatives Calculator

## Purpose and outcome
Given a financing need and documented terms for each alternative, deterministically compute the
cost and impact metrics side by side — annual interest, amortized fees, all-in annual cost,
effective cost rate, total cost over term, and equity dilution. A successful output is a factual
comparison worksheet an analyst uses; the choice and all advice remain the banker's.

## Use when
- "Compare the cost of these financing options", "all-in cost of a term loan vs a bond".
- "Model the dilution from an equity raise", "build a financing-alternatives worksheet".
- An analyst needs a consistent, reproducible cost comparison.

## Do not use
- The user wants a **recommendation** ("which is cheapest/best", "what should we do") → out of
  scope; the banker advises.
- The user wants the **debt-stack/maturity map** → route to `capital-structure-maturity-mapper`.
- Complex derivative/hedge pricing → `pricing-hedging-scenario-calculator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a worksheet with a durable `calc_id`;
it does not recommend or rank.

## Inputs and prerequisites
- The **request** (amount_needed, currency, as_of) and **alternatives** (type + terms: rate_pct,
  fees_pct, term_years for debt; share_price, current_shares for equity). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- All terms are documented inputs; the calculator does not source market rates. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Terms come from the documented deal
inputs; the worksheet records each term used per alternative.

## Workflow
1. **Validate input** — run `validate_input`; confirm the amount and each alternative's terms.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per alternative,
   interest, amortized fees, all-in annual cost, effective rate, total-over-term, and (equity)
   shares issued + dilution.
3. **Assemble the worksheet** — a row per alternative with every metric and the terms used.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   per-row cost tie-outs, the no-recommendation screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a row's total-over-term does not reconcile
to interest × term + fees, or the text ranks/recommends an option, **fix or fail closed**.

## Human approval
`external-delivery`: the worksheet may be produced, but external delivery requires human
sign-off; no recommendation is ever made by this skill.

## Failure handling
- **Missing term** (rate/term/fees for debt; price/shares for equity) → mark that metric
  not-computable; never assume a market rate.
- **Mixed currencies** → do not combine; keep the request currency and flag mismatches.
- **Zero/negative denominators** (e.g., zero shares) → flag; do not divide.
- **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — request amount, currency, as_of, number of alternatives.
2. **Per alternative** — type, terms used, annual interest, amortized fees, all-in annual cost,
   effective cost %, total cost over term, (equity) shares issued + dilution %.
3. **Data gaps / not-computable metrics.**
4. **Machine-readable** — rows + `calc_id`.
5. **Standing disclaimer** — "Illustrative cost comparison only; not a recommendation, ranking,
   or a view on which alternative to choose. The financing decision is the banker's/client's."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Enforce information barriers; deal-team only. Retain worksheet +
terms + as_of. Log read + external-delivery approval. Never cross the wall.

## Gotchas
- **Numbers are not a recommendation.** Present each alternative's metrics; never say one is
  cheapest/best.
- **All-in annual cost** amortizes upfront fees over the term — state the convention.
- **Equity has no coupon** but dilutes ownership; report dilution, never net it against interest.
- **Never rank the rows or highlight a "winner".**
