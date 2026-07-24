# Domain Rules — position-cash-reconciliation-assistant

Deterministic internal-to-external reconciliation of fund positions and cash: how records are
matched, how disagreements are classified into a fixed **break taxonomy**, how each reconciliation
line **ties out**, and how reconciling items are **proposed** (never applied). Tolerances,
materiality, the pending-settlement window, and fx rates are configuration (versioned, owned by
Asset Management operations), not hard-coded judgments.

## Reconciliation line (the unit of tie-out)

A reconciliation line is one `match_key` — one `(account, source_system, record_type,
instrument-or-currency)` combination. Positions reconcile per instrument per custody/PB account;
cash reconciles per currency per account. Internal (books) and external (custodian / prime broker /
administrator / counterparty) rows sharing a `match_key` are the two sides of that line.

## Matching (deterministic)

Records are grouped by `match_key`. Within a key, internal and external rows are sorted by
`(settle_date, record_id)` and paired positionally. For each pair, comparing the native value
(`quantity` for positions, `amount` for cash):

- values agree within the tolerance for the record type (`quantity_tolerance` / `cash_tolerance`)
  → **matched** (no break);
- values differ beyond tolerance, and the difference is attributable to a trade that settles after
  `as_of` within `pending_settlement_days` → **pending_settlement** (documented, no item);
- values differ beyond tolerance otherwise → **quantity_break** (position) or **cash_break** (cash).

Leftover rows on a key that already produced a pair are **duplicate**. Leftover rows on a key with
no counterpart at all are **missing_internal** (external-only) or **missing_external**
(internal-only) — unless the leftover row settles after `as_of` within the window, in which case it
is a one-sided **pending_settlement** (a booked-but-unsettled trade, or an accrual not yet on the
book).

## Break taxonomy

| Break type | Fires when | `break_amount` (internal − external, native) | Proposed reconciling item |
| ---------- | ---------- | -------------------------------------------- | ------------------------- |
| `quantity_break` | Matched instrument line; internal vs external quantity differ beyond `quantity_tolerance` | internal_qty − external_qty | Adjust internal book to agree to external |
| `cash_break` | Matched cash line; internal vs external balance differ beyond `cash_tolerance` | internal_amt − external_amt | Adjust internal book to agree to external |
| `missing_internal` | External record with no internal counterpart (not in transit) | − external value | Record the item on the internal book |
| `missing_external` | Internal record with no external confirmation (not in transit) | + internal value | Substantiate / reverse the internal record |
| `pending_settlement` | Difference/one-sided item explained by an unsettled trade within the cutoff | signed diff (nets at settlement) | **None** — documented reconciling item; clears at settlement |
| `duplicate` | Extra copy of a matched item on one side | ± that side's value | Reverse the duplicate |

`break_amount` is the signed native amount by which the internal book differs from the external
record because of that break. **Positions are not valued here** — a position break's
`base_impact` is `null` and its `material` flag uses `abs(break_amount) >= quantity_materiality`
(units). A cash break's `base_impact` is `break_amount` converted to base currency via the versioned
`config.fx_rates`, and it is `material` when `abs(base_impact) >= cash_materiality_base`.

## Routing (order/trade breaks)

A break whose differing/one-sided record carries `route_hint: "trade_discrepancy"` is tagged
`routing.route_to: "trade-break-resolver"`, marked `requires_correction: false`, and carries **no**
proposed item. Resolving and repairing a trade break is out of scope; it is routed, not adjusted or
booked here. The routed break still counts in the line's `breaks_total` so the line ties out.

## Tie-out invariants (enforced by `scripts/validate_output.py`)

For each reconciliation line (`match_key`):

1. `sum(break break_amount) == internal_total − external_total` — the classified breaks **fully
   explain** the difference; `residual == 0`. If a line does not tie, it fails closed.
2. Each adjusting break's `adjustment_amount == −break_amount` — the proposed item exactly offsets
   the break.
3. `corrected_internal_total` (internal + proposed adjustments) agrees to `external_total`, leaving
   only **documented** items (`pending_settlement` and routed trade breaks) outstanding:
   `corrected_internal_total − external_total == documented_or_routed_total`.

## Idempotency, lineage & durable IDs

`input_fingerprint` = SHA-256 of the normalized inputs + config. `reconciliation_id` =
`pcr-{entity}-{as_of}-{fingerprint[:8]}`. It has **no timestamp or random component**, so identical
inputs reproduce an identical reconciliation (a durable case/job id for downstream reuse and
carry-forward). Each break (`BRK-000N`) and proposed item (`PITM-000N`) is numbered deterministically
in sorted order. Every break traces to its internal/external source rows via `lineage` citations.

## Hard boundaries (fail closed)

- **Propose, never repair or move.** Every reconciling item is `status: "PROPOSED"`. The skill never
  repairs a record, adjusts a book, moves an asset/position/cash, books a trade, or transfers funds.
- **Do not decide which side is right.** A break is a disagreement to be evidenced and routed, not
  adjudicated by the skill.
- **Do not net or suppress breaks** to force a tie. If breaks do not explain the difference, surface
  the residual rather than fabricating a plug.
- **Do not value positions or select prices.** Position materiality is in units; price/valuation
  issues route to `investment-vendor-feed-reconciler` / `valuation-exception-packet`.
- **No investment advice.** The skill never recommends a buy/sell/rebalance or comments on strategy.
- **Config is a versioned contract**, never tuned per-reconciliation to make a break disappear.
- **Pending settlements are documented, not adjusted** — proposing an item for an unsettled trade
  would double-count it after settlement.
