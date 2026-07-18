# Source Map — settlement-report-summarizer

All figures in the summary must cite one of the sources below, ranked. See the shared
platform services in [`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Processor / acquirer / gateway settlement report** for the period (books-and-records payout of record) | Gross sales, refunds, chargebacks, fees, adjustments, reserves, net funded, funding date | Read-only |
| 2 | **ISO 20022 bank statement** (`camt.053` booked / `camt.054` debit-credit notification) or bank funding advice | Confirming the credited net amount and value date | Read-only (ISO 20022 parser) |
| 3 | **Card-network / scheme fee schedules and interchange tables** | Labeling and classifying fee lines (interchange vs. scheme vs. processor markup) | Read-only (approved-source retrieval) |
| 4 | Merchant-provided export/PDF of the same report | Only when 1-2 unavailable; must be labeled as unverified | Read-only (document-intelligence) |

Never let a merchant assertion (or a screenshot of an expected amount) override the
processor's settlement of record. If sources conflict, present both with citations and stop
for human review rather than picking a winner.

## Citation format

Each category and figure carries a citation of the form `{system}:{ref}@{as_of}` — e.g.
`settlement:report=STL-2026-06-0042;section=fees;type=interchange@2026-06-30` or
`camt053:stmt=...;ntry=...@2026-07-02`. The machine-readable output stores the citation per
category line; the narrative references figures that trace back to those citations.

## Freshness / effective dates

- Every line carries the report's **as-of / settlement date**; the summary states a single
  settlement (one `report_id`). Do not merge multiple settlement batches or funding dates.
- The **funding date** (value date) is separate from the settlement/period end; state both.
- Fee classification uses the **effective** interchange/scheme schedule for the period; if a
  fee line cannot be classified, label it `other_fees` rather than guessing a category.

## Least-privilege operations (deployment)

- `settlement.read(merchant_id, report_id)` → normalized settlement lines (bounded page size).
- `bank.statement_read(account_id, value_date)` → `camt.053/054` entry for the net credit.
- `refdata.fee_classify(fee_code, scheme, as_of)` → interchange / scheme / processor label.
All read-only, deterministic schemas, durable `snapshot_id`, below the fixed timeout.
