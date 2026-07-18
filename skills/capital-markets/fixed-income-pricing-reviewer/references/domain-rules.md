# Domain Rules — fixed-income-pricing-reviewer

Explainable fixed-income pricing-exception **checks** and how they map to a **review-priority
band**. Tolerances are configuration (versioned, owned by valuation control), not hard-coded
judgments, and never tuned to a desk or trader. The firm's independent-price-verification (IPV)
and fair-value-measurement standards, and applicable accounting guidance for the fair-value
hierarchy, take precedence over the defaults below.

## Check taxonomy

| Check | Flags when (default config) | Escalator | Evidence attached |
| ----- | --------------------------- | --------- | ----------------- |
| `mark_vs_independent` | \|submitted − independent\| price deviation > `mark_dev_bps` (default 30) | no | Submitted, independent, deviation bps |
| `spread_to_comparables` | \|instrument spread − comparable median\| > `spread_tol_bps` (default 40) | no | Instrument spread + comparable median |
| `price_movement_unexplained` | Day-over-day submitted move > `move_bps` (default 50) AND independent move < `corroboration_ratio` (default 0.5) × submitted move | no | Prior + submitted mark, both moves |
| `stale_price` | `last_price_change_date` gap ≥ `staleness_days` (default 10) OR `price_source_ts` age ≥ `source_staleness_days` (default 4) | **yes** | Last-change date + source timestamp |
| `liquidity_adj_plausibility` | Applied liquidity/bid-offer adjustment outside the configured band for the instrument's liquidity bucket | no | Applied adj + bucket band + quoted half-spread |
| `fair_value_level_inconsistent` | Assigned FV level inconsistent with documented input observability (L1 not observable; L2 unobservable; L3 fully observable) | **yes** | Assigned level + observability + expected level |
| `comparable_support_thin` | Comparable count < `min_comparables` (default 3) OR spread dispersion (max−min) > `max_comp_dispersion_bps` (default 60) | no | Comparable count + dispersion |

Checks are **additive and independent**; the output reports each that flagged with its own
evidence. A check whose inputs are missing is reported `not_evaluable`, never silently passed.
There is no opaque composite "pricing score".

Bps conventions: price deviations/moves are expressed in bps of the reference price
(`|a−b|/|b|·10000`); spreads are `(yield − benchmark_yield)·100` bps compared against the
comparable median.

## Priority mapping (deterministic, documented)

Per focal instrument:

| Suggested band | Rule |
| -------------- | ---- |
| **Informational** | 0 checks flagged |
| **Review** | 1–2 checks flagged, none of them an escalator |
| **Elevated** | ≥ 3 checks flagged, OR any escalator (`stale_price` / `fair_value_level_inconsistent`) flagged |

The **overall** suggested priority is the highest band across the focal instruments. Priority is
a **triage suggestion for a human reviewer**. It is not a valuation determination, a price
approval, or an IPV sign-off, and it never changes, overrides, or books a mark.

## Hard boundaries (fail closed)

- Never state or imply that a mark **is** correct, accurate, "fair value", a "mismark", or
  "confirmed mispricing" — describe deviations factually and attribute conclusions to the human
  reviewer.
- Never approve, override, restate, or book a mark, and never sign off IPV or waive an exception.
- Never assert **intent** (e.g., "marking to hit P&L") — that is a conduct determination for
  surveillance and a human.
- Never tune tolerances to the desk/trader or infer "what's normal for this book" beyond the
  configured checks.

## Benign-explanation prompts (always include when any check flagged)

A genuine idiosyncratic move (issuer news, rating action, coupon/call event); a benchmark or
curve shift the comparable set has not yet reflected; an approved, documented liquidity or model
reserve for a thinly traded line; a stale vendor feed rather than a stale trader mark (verify
source timestamps); a legitimate fair-value level given documented input observability. The pack
must invite the reviewer to weigh these before challenging a mark.
