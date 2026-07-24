# Changelog — position-cash-reconciliation-assistant

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic internal-to-external position & cash reconciliation — match a fund's
  books to custodian / prime-broker / administrator / counterparty records, classify breaks, trace
  lineage, tie each reconciliation line out, and draft PROPOSED reconciling items. Draft-only; no
  record repair, no asset/cash movement, no trade booking, no adjudication, no forced tie.
- **Break taxonomy (deterministic):** `quantity_break`, `cash_break`, `missing_internal`,
  `missing_external`, `pending_settlement`, `duplicate` — each with a signed native `break_amount`,
  a base-currency `base_impact` for cash (positions are not valued: `base_impact` null), a
  materiality flag, and internal/external lineage citations (see
  `scripts/calculate_or_transform.py`).
- **Tie-out invariants (per reconciliation line / `match_key`):** classified breaks must fully
  explain the internal-vs-external difference (`residual == 0`); each adjusting item offsets its
  break; corrected internal agrees to external after proposed items, leaving only documented
  pending-settlement and routed trade breaks.
- **Routing:** order/trade discrepancies are tagged `routing.route_to: trade-break-resolver` and
  carry no proposed item — resolving/repairing trades is out of scope; price/data discrepancies
  route to `investment-vendor-feed-reconciler` / `valuation-exception-packet`; NAV tie-out to
  `nav-preparation-tie-out`.
- **Controls:** R2; hard boundary against repairing records, moving assets/position/cash, booking
  trades, forcing a tie, adjudicating which side is correct, valuing positions/selecting prices, and
  personalized investment advice (reconciling items are `status: "PROPOSED"` only); versioned-config
  tolerances/materiality/pending-window/fx; `external-delivery` approval; segregation of duties
  between preparer and the authorized human who actions the item.
- **Idempotency & durable ID:** `reconciliation_id` = `pcr-{entity}-{as_of}-{input_fingerprint[:8]}`
  (SHA-256 of normalized inputs) with no timestamp/random component; identical inputs reproduce
  identical output; the id is the durable case/job id downstream skills reuse.
- **Scripts:** `validate_input` (job schema, source_system/record_type checks, fx/matching
  warnings), the reconciliation engine, `validate_output` (per-line tie-outs, break taxonomy,
  lineage, idempotency, proposed-only + routing, R2 prohibited-action/advice screen, disclaimer).
  All stdlib-only with `--selftest`; `validate_output --selftest` computes the pack live from the
  engine so the compliant check cannot drift.
- **Evaluations:** trigger/routing, golden reconciliation tie-out across all six break types + trade
  routing, clean-tie edge, deterministic script checks, no-repair/no-move/no-advice safety on a
  non-compliant fixture + injection, and external-delivery authorization.
- **Handoffs:** downstream/route to `trade-break-resolver` (order/trade breaks),
  `investment-vendor-feed-reconciler` and `valuation-exception-packet` (price/data breaks),
  `nav-preparation-tie-out` (NAV tie-out); distinct from `gl-reconciler` (GL vs subledger) and
  `settlement-break-reconciler` (payment settlement). Repairing/actioning items is a
  human/authorized-system action.

### Pending before release
- Domain SME (fund operations) + control-owner blind review; SoD confirmation for preparer vs the
  human who actions a reconciling item.
- Confirm the versioned tolerance / materiality / pending-settlement-window / fx-rate config source
  and its owner.
- Wire read-only MCP integrations (accounting/IBOR, custodian, prime broker, administrator,
  counterparty, config) at deployment.
