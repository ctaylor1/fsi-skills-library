# Domain Rules — credit-surveillance-packet

Orientation: standard credit-surveillance practice (leverage, coverage, liquidity, maturity
wall, spreads, reported ratings, covenant-change tracking). The firm's **packet template** and
**metric/threshold config** are versioned contracts and take precedence over these defaults.
All figures are illustrative ($mm unless noted); tolerances and thresholds are configurable.

## Credit metrics (deterministic — `scripts/calculate_or_transform.py`)

| Metric | Identity |
| ------ | -------- |
| `gross_leverage_x` | `gross_debt / ebitda` |
| `net_leverage_x` | `(gross_debt - cash) / ebitda` |
| `interest_coverage_x` | `ebitda / interest_expense` |
| `fccr_x` (fixed-charge proxy) | `(ebitda - capex) / interest_expense` |
| `total_liquidity` | `cash + undrawn_revolver` |
| `near_term_maturities` | sum of maturities with `year <= as_of_year + near_term_years` (default 2) |
| `liquidity_covers_near_term` | `total_liquidity >= near_term_maturities` |
| `spread_delta_bps` | `current_bps - prior_bps` (widening when > 0) |

`EBITDA == 0` or `interest_expense == 0` are rejected at input (ratios undefined). The FCCR is a
documented proxy; a deployment config may extend it to include scheduled principal.

## Tie-outs (deterministic block)

Where the request supplies analyst/vendor-stated values, the computed ratio must reconcile
within tolerance `TOL = 0.05`:

| Tie-out | Checked against |
| ------- | --------------- |
| `gross_leverage_x` | `stated_gross_leverage_x` |
| `net_leverage_x` | `stated_net_leverage_x` |
| `interest_coverage_x` | `stated_interest_coverage_x` |

A mismatch beyond tolerance is a **block** (`tie-out-break`): the packet may not restate a
figure the computation does not support.

## Period-over-period change (surface, never judge)

Change vs the prior period is **reported as disclosure**, never as a recommendation:

- `net leverage` rose `>= leverage_increase_alert_x` (default 0.25x) → **warn** `leverage-increase`.
- `interest coverage` fell `>= coverage_decline_alert_x` (default 0.25x) → **warn** `coverage-decline`.
- `spread` widened `>= spread_widening_alert_bps` (default 50 bps) → **warn** `spread-widening`.
- `total_liquidity` does not cover near-term maturities → **warn** `near-term-maturity-liquidity-gap`.
- an agency `rating/outlook` changed vs prior → **warn** `rating-change-reported` (reported, not assigned).

Warn (disclosure) flags do **not** block the packet; they are surfaced for the human analyst.

## Ratings (reported, never assigned)

Agency ratings and outlook are **reported** from the rating-agency source with the prior value
and a `changed` flag. This skill **never** assigns, derives, implies, or opines on a rating
level — that is a human/agency process. A rating claim must cite a `rating-agency` source that
is marked **approved**.

## Covenant changes (flag, then hand off)

The packet flags **which** covenant items changed vs the prior period (from the credit
agreement). It does **not** extract full covenant terms (definitions, baskets, step-downs) and
does **not** determine compliance or headroom. A changed covenant is routed to
`credit-terms-covenant-extractor` for term detail and to a human for any compliance
determination.

## Traceability (no unsupported/unapproved claims)

Every metric group, spread, rating, maturity source, and covenant flag must cite a `source_id`
present in `sources[]`:

- Unknown `source_id` → **block** (`unsupported-claim`).
- A `market` or `rating-agency` source not marked **approved** → **block** (`unapproved-source`).

## Hard boundaries (fail closed)

- **Draft only.** Never send, circulate, email, submit, or mark a packet final.
- **No rating assignment.** `rating_action` is always `reported-only`; the skill never assigns
  or derives a credit rating.
- **No thesis change.** `thesis_action` is always `unchanged`; the skill never forms, alters, or
  restates an investment thesis.
- **No position/trade view.** `position_action` is always `none`; the skill never recommends or
  changes a position or trade, and gives no personalized investment advice.
- **No covenant interpretation.** Flag a covenant change; never determine compliance/headroom or
  extract terms — that is `credit-terms-covenant-extractor` and a human.
- **No fabrication.** Never invent a figure, spread, comp, rating, or covenant conclusion.

## Required approvals before delivery

`preparer` (credit research analyst) and `reviewer` (sector lead / desk) sign-offs must be
**recorded** (by humans) before the draft may be delivered. The rating, thesis, and position are
never set by this skill.
