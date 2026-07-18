---
name: margin-collateral-optimizer
description: >-
  Analyze open margin calls against eligible collateral — applying agreement eligibility and
  haircuts, per-call concentration limits, liquidity, and funding/pledge cost — and recommend
  a cheapest-to-deliver allocation with post-haircut coverage, a funding-cost estimate, and
  any surfaced shortfalls. Use when a collateral manager or treasury analyst asks "how should
  I meet these margin calls", "what is the cheapest collateral to post", "optimize collateral
  allocation across these CSAs", or "which assets are eligible and what coverage do I get".
  This skill produces a recommendation for treasury and operations review only; it NEVER
  pledges, posts, moves, substitutes, or settles collateral, NEVER disputes, accepts, or
  rejects a margin call, and makes no binding funding decision or investment advice — those
  are human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires post-trade/clearing, market & reference data, collateral-inventory/custody, funding-curve, and versioned eligibility/limit-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Collateral manager / treasury analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Margin & Collateral Optimizer

## Purpose and outcome
Given a set of open **margin calls** and the firm's **collateral inventory**, compute an
explainable, **cheapest-to-deliver** allocation of eligible collateral to each call — subject
to agreement eligibility, haircuts, and per-call concentration limits — and report post-haircut
coverage, an annualized funding-cost estimate, and any **shortfalls or breaches surfaced**, not
hidden. A successful output lets a collateral manager or treasury analyst see *which eligible
assets to post to which call, at what coverage and cost, and what remains unresolved* — so a
human can review, approve, and instruct. The decision and any collateral movement remain human.

## Use when
- "How should I meet these margin calls with the collateral I have?"
- "What is the cheapest collateral to post to CCP-ALPHA / this CSA?"
- "Optimize the allocation across these agreements and show me the coverage and funding cost."
- "Which of my assets are eligible for this call, and where am I short?"

## Do not use
- The user wants to **pledge, post, move, substitute, or settle** collateral, or to **dispute,
  accept, or reject** a margin call → out of scope. Produce the recommendation and route to
  treasury and operations (human) who instruct in the collateral-management/settlement system.
- A **binding funding decision** (repo, borrow/lend, FX to raise cash) or **personalized
  investment advice** → out of scope; not this skill and not any skill without a human gate.
- **Settlement of an approved movement** → `post-trade-settlement-monitor`; a **failed/broken
  movement** → `settlement-break-reconciler`.
- **Counterparty/CCP exposure** analysis → `counterparty-exposure-monitor`; **funding/liquidity
  stress** of the plan → `liquidity-risk-scenario-analyzer`; a **corporate action** on a pledged
  security → `corporate-action-election-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a recommendation with a
durable `recommendation_id`; downstream settlement, break, exposure, and liquidity skills consume
it after treasury/operations approve and execute. It must not duplicate their execution or their
case states, and it never instructs a collateral movement or a margin-call response itself.

## Inputs and prerequisites
- **Margin calls** — each with `call_id`, `agreement_id`, `call_type` (VM/IM), `required_amount`
  (post-haircut value demanded), `currency`, and `eligible_asset_classes`.
- **Collateral inventory** — each asset with `asset_id`, `asset_class`, `market_value`,
  `available_value` (unencumbered), `currency`, and `pledge_cost_bps` (opportunity cost).
- **Haircut / eligibility schedule** — per `(agreement_id, asset_class)`: `haircut` and
  `eligible`. **Concentration-limit config** and a `config_version`.
- Read access to post-trade/clearing, collateral inventory, market/reference data, the funding
  curve, and the versioned eligibility/limit config. Schema and validation:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **CSA / clearing rulebook** is the
authority on eligibility and haircuts; the **collateral inventory** is the position of record for
what is available. Never substitute a trader's or counterparty's assertion for the agreement
terms. Cite every allocation line to the inventory row **and** the haircut-schedule entry.

## Workflow
1. **Scope & validate** — confirm the portfolio, `as_of`, and the open calls; load inventory and
   the versioned schedule/limits; run `validate_input` (fails closed on structure, warns on
   eligibility gaps and infeasible coverage).
2. **Allocate (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): process calls
   most-constrained-first, post eligible assets cheapest-to-deliver, respect the per-class
   concentration cap, and fill to `required_amount`. Each line carries its evidence + citation.
3. **Compute coverage & cost** — post-haircut coverage ratio, shortfall, and an annualized
   funding-cost estimate per call and for the portfolio.
4. **Surface the unresolved** — collect every shortfall and concentration breach into
   `unresolved_items`; report eligibility gaps as notes. Never hide an uncovered call.
5. **Write the pack** — plain-language recommendation per call (what to post, coverage, cost,
   cited) + the unresolved items + the standing disclaimer + the treasury/operations approval gate.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: every allocation line is cited; coverage math ties out per call; every
shortfall/breach is surfaced; no execution/decision/dispute/advice language is present; the
disclaimer is present; and `approval_required` is true. Fail closed on any miss.

## Human approval
`external-delivery`: **treasury and operations** approval is required before the recommendation
is delivered as an instruction or written to a system of record. No approval is needed for the
analyst's own read. The skill never pledges, moves, or settles collateral and never answers a
margin call.

## Failure handling
- **Infeasible coverage** (eligible post-haircut inventory < required) → post what is eligible
  and surface the shortfall; do not overstate coverage or invent eligibility.
- **Missing/stale schedule** → stop; a recommendation on a superseded eligibility/haircut schedule
  is invalid. Record the `config_version` used.
- **Ambiguous portfolio/agreement** → confirm; never allocate against the wrong CSA.
- **Concentration cap binds** → leave the call short and flag the breach rather than exceeding the
  limit.
- **Tool timeout** → return calls allocated so far with a clear "incomplete" flag; do not assume
  retries or step-up authorization.

## Output contract
1. **Summary** — portfolio (masked), `as_of`, calls covered/short, total funding-cost estimate.
2. **Per-call recommendation** — recommended allocation lines (asset, posted market value,
   haircut, post-haircut value, pledge cost, concentration %, citation), coverage ratio, shortfall.
3. **Unresolved items** — uncovered calls and concentration breaches, first.
4. **Eligibility notes** — eligible classes with no schedule entry / not deliverable.
5. **Machine-readable** — the calculate_or_transform core + `recommendation_id` for downstream skills.
6. **Standing disclaimer** — "Recommendation only; not a collateral instruction. No collateral has
   been pledged, moved, substituted, or settled, and no margin call has been disputed or accepted.
   Treasury and operations approval is required before any action."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential. Positions, counterparties, and agreements are sensitive — minimize to what
the recommendation requires and mask account/portfolio identifiers where shown. Retain the
recommendation + citations + `config_version` per records policy; log the read and any
external-delivery approval. Never exfiltrate position or counterparty data.

## Gotchas
- **A recommendation is not an instruction.** The allocation justifies a *treasury/operations
  decision*, never a collateral movement or a margin-call response.
- **Cheapest-to-deliver ≠ lowest haircut.** The ordering keys on `pledge_cost_bps` (opportunity
  cost) first; a low-haircut asset the firm needs for liquidity may be the *wrong* one to post.
- **Most-constrained-first matters.** Allocating a cash/UST-only IM call before a broadly-eligible
  VM call prevents needless starvation and false shortfalls.
- **Surface, do not hide.** A shortfall or concentration breach must appear in `unresolved_items`;
  silently relaxing a limit or eligibility rule is prohibited.
- **Schedules are versioned contracts.** Eligibility, haircuts, and limits come from the approved
  config, never from guessing what "should" be eligible; record the `config_version`.
- **Funding cost is an estimate.** It informs a human decision; it is not advice to trade and
  carries no guarantee.
