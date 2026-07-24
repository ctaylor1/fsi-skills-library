# Controls — position-cash-reconciliation-assistant

- **Risk tier:** R2 — analytical / drafting. **Action mode:** Draft-only; no system-of-record
  change.
- **Human approval:** `external-delivery` — required before the reconciliation or any proposed
  reconciling item is delivered externally or written to a system of record. Internal analytical use
  may be reviewer-sampled.

## Prohibited (fail closed)

- **No repair / no move.** The skill never repairs or adjusts a record, moves an asset, position, or
  cash, books a trade, or transfers funds in any book of record or external system. Reconciling
  items are **proposals only** (`status: "PROPOSED"`).
- **No forced tie.** No plug, netting, or suppression of breaks to make a line appear to tie. If
  classified breaks do not explain a line's difference, surface the residual.
- **No adjudication.** The skill does not decide which side (internal book or external record) is
  correct, nor approve its own proposed items.
- **No trade resolution.** Order/trade breaks are routed to `trade-break-resolver`; the skill does
  not resolve, repair, or book trades.
- **No valuation / price selection.** The skill does not value positions or choose a price; price and
  data discrepancies route to `investment-vendor-feed-reconciler` / `valuation-exception-packet`.
- **No investment advice.** The skill never makes a personalized investment recommendation
  (buy/sell/rebalance/allocate) or comments on strategy — an R2 universal prohibition.
- **No per-reconciliation threshold tuning.** Tolerances, materiality, the pending-settlement window,
  and fx rates come only from the versioned `config`.

## Required output screens (`scripts/validate_output.py`)

- **Tie-out (per line):** `sum(break break_amount) == internal_total − external_total`,
  `residual == 0`, corrected internal agrees to external after proposed items, leaving only
  documented pending / routed items.
- **Break taxonomy:** every break's `type` is in the fixed set {`quantity_break`, `cash_break`,
  `missing_internal`, `missing_external`, `pending_settlement`, `duplicate`} with an id,
  `break_amount`, `unit`, and `material` flag.
- **Lineage:** every break cites its internal/external source rows (`internal:` / `external:`
  prefix).
- **Idempotency:** `reconciliation_id` is derived from `entity/as_of/input_fingerprint` with no
  timestamp/random component; `input_fingerprint` is a 64-hex content hash.
- **Proposed-only + routing:** every reconciling item has `status: "PROPOSED"` and offsets its
  break; `pending_settlement` carries none; order/trade breaks route to `trade-break-resolver` with
  no item.
- **Prohibited-action/advice screen (R2):** no record-repair, asset-movement, posting/booking, or
  investment-advice language anywhere (a break is evidenced, never actioned).
- **Disclaimer:** the standing no-repair / no-move disclaimer is present.

## Segregation of duties

- The skill **prepares** the reconciliation and **proposes** reconciling items. A different,
  authorized human (operations reviewer / controller) **reviews, approves, and actions** the change
  in the book of record or instructs the external agent. Preparation and action must not be the same
  actor.
- The reconciliation preparer is not the item approver, and neither is the skill.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Position and cash detail can reveal fund
  strategy and holdings; minimize to what evidences a break and restrict on a need-to-know basis. Do
  not compile holdings across funds beyond the reconciliation scope.
- Retain the reconciliation, breaks, lineage, proposed items, and `config_version` per records
  policy; log the read and any external-delivery approval.

## Reproducibility

`reconciliation_id` + `input_fingerprint` bind the output to the exact inputs and config version;
re-running the same inputs reproduces the same breaks, proposed items, and per-line tie-out.
