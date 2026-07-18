# Domain Rules — margin-collateral-optimizer

How eligible collateral is allocated to margin calls, and how coverage, concentration, and
funding cost are computed. Eligibility, haircuts, and concentration limits are **configuration
(versioned, owned by treasury / collateral-management)**, not hard-coded judgments, and are
never tuned to a desired outcome. The relevant CSA / clearing rulebook and the firm's
collateral standard take precedence over anything here.

## Inputs (per `scripts/validate_input.py`)

- **Margin calls** — `required_amount` is the collateral **value** (post-haircut) the call
  demands, with `call_type` (VM/IM), `agreement_id`, `currency`, and `eligible_asset_classes`.
- **Collateral inventory** — each asset's `asset_class`, `market_value`, `available_value`
  (unencumbered), `currency`, and `pledge_cost_bps` (annualized opportunity cost of posting).
- **Haircut schedule** — per `(agreement_id, asset_class)`: `haircut` (fraction) and
  `eligible` (bool). An asset is deliverable to a call only if its class is on the call's
  `eligible_asset_classes` **and** the schedule marks it `eligible` for that agreement.

## Allocation method (deterministic — see `scripts/calculate_or_transform.py`)

1. **Most-constrained-first call order.** Process calls by fewest eligible asset classes,
   then largest `required_amount`, then `call_id`. This prevents a broadly-eligible call from
   starving a narrowly-eligible one of scarce inventory (e.g. a cash/UST-only IM call).
2. **Cheapest-to-deliver within a call.** Among eligible assets with stock remaining, post in
   ascending `pledge_cost_bps`, then ascending `haircut`, then `asset_id`. This delivers the
   assets the firm gives up the least by pledging, preserving scarce high-cost / highly-liquid
   inventory (cash, equities) for where it is needed.
3. **Post-haircut coverage.** Each posted lot contributes `post_haircut_value =
   posted_market_value * (1 - haircut)`. Fill until the call's `required_amount` is met; the
   final lot may be posted partially to hit the requirement exactly.
4. **Concentration cap.** No asset class may cover more than `max_asset_class_pct_per_call`
   of a call's requirement (post-haircut). If the cap binds and other eligible inventory is
   exhausted, the call is left short.
5. **Shortfall & funding cost.** `coverage_ratio = total_post_haircut_value / required_amount`;
   `shortfall = max(0, required - covered)`. `funding_cost_annual_estimate =
   Σ posted_market_value * pledge_cost_bps / 10,000` — an **estimate**, not advice.

Assets are consumed across calls: inventory posted to an earlier (more constrained) call is
not available to a later one.

## Surfacing rules (fail closed)

- A call with `shortfall > tolerance` or any `concentration_breaches` **must** appear in
  `unresolved_items`. The recommendation never hides an uncovered call or silently relaxes a
  limit or eligibility rule.
- An eligible asset class with no matching haircut-schedule entry is reported as an
  `eligibility_note`, not treated as deliverable.

## Hard boundaries (fail closed)

- Never **pledge, post, move, substitute, or settle** collateral, and never stage such an
  instruction — recommend only.
- Never **dispute, accept, or reject** a margin call, and never make a **binding funding
  decision** or give **personalized investment advice** / guaranteed-return claims.
- Never **override eligibility or haircuts** beyond the versioned schedule, and never tune
  concentration limits to reach a desired allocation.
- Treat the funding-cost figure as an **estimate for a human decision**, not a
  recommendation to trade.

## Output priority (what the reviewer sees first)

1. Uncovered calls and concentration breaches (`unresolved_items`) — highest priority.
2. Per-call recommended allocation with coverage, cited to inventory + haircut schedule.
3. Portfolio funding-cost estimate and the standing disclaimer.

The recommendation is a **decision-support artifact for treasury and operations**. It is not
an instruction and it never triggers a collateral movement or a margin-call response.
