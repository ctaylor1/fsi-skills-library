# Bounded domain methods

## twr

Chain geometrically contiguous subperiod returns from valuations at every external-flow boundary. Opening-after-flow values must equal the previous closing-before-flow plus boundary flow. The final post-period flow is zero.

## modified_dietz

Compute (ending minus beginning minus net flows) divided by beginning plus day-weighted end-of-day flows. Nonpositive denominator is unavailable; this is a money-weighted period estimate, not exact TWR.

## money_weighted

Annual ACT/365 investor-sign XIRR including terminal value. Net same-day flows, require one negative-to-positive sign transition, then bisect over [-0.999999,1000000]. Nonconventional signs, out-of-domain roots or nonconvergence are unavailable.

## Interpretation and exclusions

Source valuations, external-flow completeness and fee basis need performance-owner review. No benchmark attribution, valuation, composite construction or performance advertising approval.

Ratios and linked growth factors round to24 decimal places. XIRR uses80-digit numerical arithmetic, at most512 bisections, rate interval tolerance1e-24, relative NPV tolerance1e-24 scaled by max(total absolute flows,1), and maximum36525-day horizon.

Use the supplied approved method and policy version; this package does not infer professional approval from source strings. Effective/expiry dates are enforced for referenced sources. Unknown evidence stays unavailable or rejects the input. Multiple modes are separate workpapers; do not add their outputs as if they were independent contributions.
