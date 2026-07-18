# Source Map — trade-confirmation-explainer

Every figure and field in the explanation must cite one of the sources below, ranked. See
the shared platform services in [`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Post-trade / clearing** record of the executed trade (books-and-records) | Trade/settlement dates, quantity, price, capacity, net amount, fees | Read-only |
| 2 | The **customer trade confirmation** document itself (Rule 10b-10) | Field-by-field disclosures, page/line citations | Read-only (document-intelligence) |
| 3 | **OMS/EMS** order/execution record | Execution price, venue, capacity corroboration | Read-only |
| 4 | **Reference/market data** | Instrument identity (CUSIP/ISIN/ticker), security type, day's price context | Read-only |
| 5 | User-provided copy of the confirmation | Only when 1–4 unavailable; label as unverified | Read-only |

Never let a user assertion override the books-and-records confirmation. If the document and
the clearing record conflict, present both with citations and stop for human review — do not
silently pick one.

## Citation format

Each field carries a citation of the form `{system}:{ref}@{as_of}` — e.g.
`confirmation:conf=CNF-2026-07-15-0001;p1@2026-07-15` or
`clearing:trade=TRD-8842;line3@2026-07-15`. The machine-readable output stores a citation per
key figure (principal, net_amount, charges); the narrative references them inline where a
number is stated.

## Freshness / effective dates

- Explain the confirmation **as issued**; state the trade date and settlement date verbatim.
- If reference data resolves an identifier or security type that the document is silent on,
  cite the reference-data source separately and label it as enrichment, not a disclosure.
- Settlement-cycle context (US standard T+1 since 2024-05-28) is background, not a figure to
  assert as if printed on the confirmation unless it appears there.

## Least-privilege operations (deployment)

- `confirmation.read(confirmation_id)` → the disclosed fields + document citations.
- `clearing.read_trade(trade_id)` → books-and-records trade/settlement record.
- `refdata.resolve(instrument_id)` → instrument identity / security type.
All read-only, deterministic schemas, durable `explanation_id`, below the fixed timeout.
