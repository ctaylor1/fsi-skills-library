# Domain Rules — trade-confirmation-explainer

The rules and arithmetic this skill applies when explaining a US securities trade
confirmation. These are **descriptive**: they identify and reproduce what the confirmation
already discloses. They never grade the trade, price, or charges (see
[controls.md](controls.md)). US default; configure jurisdiction packs per deployment.

## Rule 10b-10 disclosures to identify and explain

A customer confirmation under SEC Rule 10b-10 typically discloses, and the explanation should
cover, each of these where present:

| Field | Plain-language meaning |
| ----- | ---------------------- |
| Trade date | Date the order executed |
| Settlement date | Date cash/securities change hands (US standard **T+1** since 2024-05-28) |
| Side | Buy or sell |
| Capacity | Whether the firm acted as **agent** (broker, for a commission) or **principal** (dealer, trading from its own account) |
| Quantity & price | Shares/units and the execution price per unit |
| Principal amount | quantity × price × price_factor |
| Commission | Agency charge (principal-capacity trades show markup/markdown instead) |
| Markup / markdown | Dealer compensation on principal trades; disclosed for many trades, embedded in the price |
| Fees | Regulatory and pass-through fees (e.g. SEC Section 31 fee on sells, FINRA TAF) |
| Accrued interest | On bond trades, interest the buyer pays the seller for the current coupon period |
| Yield | On debt securities, the yield disclosure Rule 10b-10 requires |
| Net amount | Total the customer pays (buy) or receives (sell) |

## Canonical money tie-out (deterministic)

Implemented in `scripts/calculate_or_transform.py` and re-checked by
`scripts/validate_output.py`:

```
principal     = quantity * price * price_factor
charges_total = commission + fees_total
direction     = +1 for buy, -1 for sell
expected_net  = principal + accrued_interest + direction * charges_total
```

- **Buy** debits the customer: `net = principal + accrued + charges_total`.
- **Sell** credits the customer: `net = principal + accrued - charges_total`.
- **Markup / markdown** on principal trades are **already embedded in the price/principal**
  and are disclosed, not re-added — otherwise charges would be double-counted.
- `price_factor` normalizes quoting conventions: `1.0` for equities; `0.01` for bonds quoted
  per 100 face; contract multipliers for options/futures.
- Tolerance is one cent; a miss **fails closed** for re-check, it is never rounded away.

## Capacity, fees, and settlement notes

- **Agent vs principal** changes how the firm is paid: agency → commission line; principal →
  markup/markdown embedded in price. State which one applies; do not imply one is better.
- **SEC Section 31 fee** and **FINRA TAF** generally apply to **sales**, not purchases; a buy
  with no such fee is normal, not an omission.
- **Settlement cycle**: US cash-equity/corporate-bond standard is **T+1**; some products
  (e.g. certain new issues, money-market instruments) differ. Only state the printed
  settlement date; use the cycle as background, not as an assertion about correctness.

## Hard boundary (never do)

Explaining *what* a field means and *what* number is printed is in scope. Saying the price was
good/bad, the commission was too high, the trade was suitable/unsuitable, or that the
confirmation is erroneous is **out of scope** — that is advice or a determination. Surface the
facts with citations and route judgment questions per [handoffs.md](handoffs.md).
