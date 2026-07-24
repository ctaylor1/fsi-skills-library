---
name: transaction-cost-estimator
description: >-
  Estimate the transaction cost of an executed or contemplated order — half-spread,
  commissions/fees, market impact, delay (implementation-shortfall) cost, and opportunity
  cost of unfilled quantity — using a validated, versioned methodology with explicit
  uncertainty ranges, and produce a source-linked TCA workbook. Use when a trading or
  execution-quality analyst asks to "estimate transaction cost", "run TCA", "what was the
  slippage/market impact", or "cost of this trade in bps". HARD BOUNDARY: R2 draft-only — it
  NEVER routes, executes, cancels, or amends an order, never selects or recommends a venue,
  broker, or algo, and never asserts best execution; it estimates costs for human review.
  Routes execution-quality/best-ex review to best-execution-reviewer.
license: MIT
compatibility: Amazon Quick Desktop; requires OMS/EMS execution records, market/reference data (arrival/VWAP/close, ADV, volatility), and the approved TCA-methodology config (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Trading analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Transaction Cost Estimator

## Purpose and outcome
Decompose the cost of a trade into transparent, reproducible components (half-spread,
commissions, market impact, delay/implementation-shortfall, opportunity cost) in basis points
and currency, with an explicit uncertainty range and the methodology version used. A
successful output gives a trading/execution-quality analyst a defensible cost estimate — it
never routes, executes, or judges best execution.

## Use when
- "Estimate transaction cost / run TCA on this order", "what was the slippage / market impact".
- "Cost of trading N shares in bps under our methodology".

## Do not use
- The user wants to **route, execute, cancel, or amend** an order, or pick a **venue/algo/
  broker** → out of scope; the trader/OMS acts.
- **Best-execution / venue-quality** obligation review → `best-execution-reviewer`.
- **Order-allocation** validation → `order-allocation-validator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a TCA workbook with a durable
`tca_id`; it does not act on the market or judge execution quality.

## Inputs and prerequisites
- The order + execution: side, quantity, arrival price/time, executed price/quantity, VWAP,
  close, ADV, volatility. Approved **TCA-methodology config** (impact model + coefficients,
  spread/commission assumptions), versioned. Schema:
  [scripts/validate_input.py](scripts/validate_input.py) and
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Execution record is the system of
record; market data supplies benchmarks; methodology from versioned config. Cite every input.

## Workflow
1. **Validate input** — run `validate_input`.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): each cost component
   from the versioned methodology, signed by side, plus a model-uncertainty band. Components
   sum to the total.
3. **Assemble the workbook** — components (bps + currency), total, uncertainty range,
   methodology version, and assumptions/limitations.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   component tie-out, methodology-version presence, the no-execution/no-venue-advice screen,
   and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If components don't sum to the total, the
methodology version is missing, or the text contains execution/venue-advice language, **fix or
fail closed**.

## Human approval
`external-delivery`: human review before the TCA is delivered externally or written to a
system of record. No market action is ever taken.

## Failure handling
- **Missing benchmark/ADV/volatility** → compute only the supported components; label the rest
  "not evaluable"; never invent an impact coefficient.
- **Zero/again ADV or price** → guard division; flag as not-evaluable rather than dividing by zero.
- **Stale/conflicting market data** → cite both; flag. **Tool timeout** → partial + incomplete.

## Output contract
1. **Summary** — order (masked), side, qty, methodology version, total cost (bps + currency),
   uncertainty range.
2. **Components** — half-spread, commission, market impact, delay, opportunity cost (each bps +
   currency, cited).
3. **Assumptions & limitations; data gaps.**
4. **Machine-readable** — components + `tca_id`.
5. **Standing disclaimer** — "Estimated transaction cost for review only; not execution, venue,
   broker, or best-execution advice. No order has been routed, executed, or amended."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account/order identifiers. Retain the TCA + citations + methodology
version. Log read + external-delivery approval.

## Gotchas
- **Sign by side.** A cost is positive when execution is worse than the benchmark for the
  order's side; do not report a favorable print as a cost of the wrong sign.
- **Uncertainty is required.** Market-impact is an estimate with a band; a single point value
  presented as exact is misleading.
- **bps and currency must agree.** currency = bps/10000 × notional; the output validator ties
  them out.
- **TCA is not best-ex.** Estimating cost is in scope; judging whether execution met best-ex
  duty is `best-execution-reviewer`.
