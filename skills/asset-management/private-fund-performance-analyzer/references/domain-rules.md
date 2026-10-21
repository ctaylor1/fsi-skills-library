# Bounded domain methods

## investor_net

DPI=distributions/paid-in, RVPI=residual NAV/paid-in, TVPI=(distributions+residual NAV)/paid-in. Zero paid-in yields unavailable multiples. Add residual NAV as terminal investor cash flow for conventional annual XIRR.

## Interpretation and exclusions

Do not substitute undrawn commitments for paid-in capital, distributions for realized gains, or residual NAV for cash. Recallable/recycled capital needs exact actual-flow mapping. No PME, synthetic no-facility return or waterfall.

Multiples round to24 decimal places. XIRR shares the80-digit ACT/365 conventional-sign solver with portfolio-performance-measurer; bounded root search and residual checks are disclosed in native output.

Use the supplied approved method and policy version; this package does not infer professional approval from source strings. Effective/expiry dates are enforced for referenced sources. Unknown evidence stays unavailable or rejects the input. Multiple modes are separate workpapers; do not add their outputs as if they were independent contributions.
