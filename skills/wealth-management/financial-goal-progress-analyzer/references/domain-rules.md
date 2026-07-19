# Domain Rules — financial-goal-progress-analyzer

How each goal is projected and banded. Assumptions (returns, inflation, thresholds) are
**approved configuration** (versioned, owned by the investment/planning committee), not
hard-coded judgments, and are never tuned to an individual. The firm's planning standard and
Reg BI care obligation take precedence.

## Projection model (deterministic)

For each goal, with monthly rate `rm = expected_return_annual / 12` and whole months to
target `n`:

- **Projected value (nominal)** = `PV·(1+rm)^n + PMT·((1+rm)^n − 1)/rm`, where `PV` is the
  dedicated balance and `PMT` is the monthly contribution (ordinary, period-end annuity).
  When `rm = 0`, projection = `PV + PMT·n`.
- **Inflation factor** = `(1 + inflation_annual)^(n/12)`.
- **Projected value (real)** = projected nominal ÷ inflation factor.
- **Comparison basis** — a `nominal`-terms target is compared to the nominal projection; a
  `real`-terms target (today's dollars) is compared to the **real** projection.
- **Funded ratio** = comparison basis ÷ target amount (same terms).
- **Shortfall / surplus** = target − comparison basis (positive = shortfall).

## Status bands (deterministic, documented)

Thresholds come from the approved assumptions (`on_track_min`, `at_risk_min`).

| Band | Rule (default thresholds) |
| ---- | ------------------------- |
| **On track** | funded ratio ≥ `on_track_min` (default 1.00) |
| **At risk** | `at_risk_min` ≤ funded ratio < `on_track_min` (default 0.85–1.00) |
| **Off track** | funded ratio < `at_risk_min` (default 0.85) |

A status band is a **triage aid for the advisor**. It is not a suitability determination, a
recommendation, or a trigger for any action.

## Illustrative planning levers (what-ifs, not advice)

Computed only for goals **not** On track, using the same approved assumptions:

- **Additional monthly contribution** — the extra level PMT that would bring `PV` to the
  target (in nominal terms) by the target date: `required_pmt − current_pmt`, floored at 0.
- **Additional months at current contribution** — extra whole months (deterministic search,
  capped at `max_extension_months`) for `PV + PMT` to reach the nominal target; `None` if the
  target is not reachable within the cap (e.g., a non-growing plan).
- **Target reduction to match projection** — how much lower the target would need to be to
  equal the current projection (i.e., the shortfall).

Levers are **arithmetic illustrations for advisor-client discussion**. They are never framed
as a recommendation, an instruction ("you should …"), or advice.

## Not-evaluable goals (fail closed, do not fabricate)

- Missing or non-positive `target_amount`.
- Missing or unparseable `target_date`.
- `target_date` not after the as-of date (already due) — progress is not projectable forward.

## Hard boundaries (fail closed)

- Never make a **recommendation** or select a product/allocation/security.
- Never make a **suitability determination** or give personalized investment/tax advice.
- Never **guarantee** results or state a goal **will** be reached — projections are estimates.
- Never **place a trade, file, post, close, or write** any system of record.
- Never **tune approved assumptions to the individual** to change a status band.
