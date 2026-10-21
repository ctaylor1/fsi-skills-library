# Bounded domain methods

## basket_control

Value each supplied constituent per creation unit, add cash balance and compare with creation-unit shares times NAV/share. Scale quantities by integral units. AP cash includes fees paid on creation and deducted on redemption; fees are outside NAV basket tie-out.

## secondary_market

For same-date positive NAV and quote values, calculate market-price premium/discount to NAV and quoted bid/ask spread divided by midpoint.

## Interpretation and exclusions

Any missing constituent price or NAV makes aggregate tie-out unavailable. Supplied AP/custom approval labels are not authenticated. Signed cash balances are allowed. In the legacy no-extension methods, derivatives, FX and calendar controls are unsupported; select the explicit specialized-basket extension for supplied-engine derivative values, FX conversion and reviewed calendar evidence. Signed constituent quantities and actual creation/redemption execution remain unsupported.

Basket/cash/quantity arithmetic exact Decimal; secondary-market ratios round to12 decimal places. Per-creation-unit tolerance excludes transaction fees.

Use the supplied approved method and policy version; this package does not infer professional approval from source strings. Effective/expiry dates are enforced for referenced sources. Unknown evidence stays unavailable or rejects the input. Multiple modes are separate workpapers; do not add their outputs as if they were independent contributions.
