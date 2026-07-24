# Adjacent-Skill Handoffs — position-cash-reconciliation-assistant

This skill produces a position/cash reconciliation with a classified break list, lineage, and
**proposed-only** reconciling items (durable `reconciliation_id`), then stops. It does not repair
records, adjust books, move assets or cash, book or resolve trades, value positions, select prices,
or strike NAV.

## Downstream / route to

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `trade-break-resolver` | A break is an **order/trade discrepancy** to be worked to resolution and repaired (not a book-only reconciling item). This skill tags such breaks `routing.route_to: trade-break-resolver` and proposes no item. | `reconciliation_id` + the routed break rows |
| `investment-vendor-feed-reconciler` | The disagreement is actually a **price / rating / index-constituent / instrument-attribute** difference between data sources, not a position/cash break | account + instrument + the differing fields |
| `valuation-exception-packet` | A break turns on a **stale, disputed, or outlier price** that must be evidenced for a valuation decision | `reconciliation_id` + the affected line |
| `nav-preparation-tie-out` | The reconciliation feeds a **NAV strike / fund-accounting tie-out** across prices, accruals, income, expenses, and shares | `reconciliation_id` + reconciled positions/cash + tie-out status |

## Upstream (may call this skill)

`nav-preparation-tie-out` sequences a fund's NAV tie-out and may request a position/cash
reconciliation as one input; it consumes the `reconciliation_id` and the per-line tie-out status.
That skill (an R3 control-decision-support workflow) — not this skill — gates the eventual NAV
strike and any accounting posting.

## Actioning the proposed items (human / authorized system)

There is **no catalog skill that repairs positions/cash or moves assets**, by design. Approved
reconciling items are actioned by an **authorized human/system in the book of record** (adjust the
book, instruct the custodian/PB, or clear at settlement) under segregation-of-duties controls. This
skill hands over `PROPOSED` items and the supporting evidence; the review, approval, and action
happen outside it.

## Not this skill (route elsewhere)

- **General-ledger control-account reconciliation** (GL vs subledger/source system) →
  `gl-reconciler` (Finance & Operations), not fund position/cash reconciliation.
- **Payment / settlement-file reconciliation** (network/acquirer/processor settlement to bank cash)
  → `settlement-break-reconciler` (Payments).
- **Order/trade break resolution and repair** → `trade-break-resolver`; this skill only classifies
  and routes such breaks.

## Duplicate-execution prevention

- This skill **classifies and evidences breaks and proposes reconciling items only**; it must not
  repair, adjust, move, book, resolve trades, value positions, select prices, adjudicate which side
  is correct, or approve its own items — those belong to the human reviewer and the downstream
  skills.
- Downstream skills reuse the `reconciliation_id`, breaks, and lineage rather than recomputing the
  match.
