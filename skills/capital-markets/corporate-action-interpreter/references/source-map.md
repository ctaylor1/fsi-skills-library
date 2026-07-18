# Source Map — corporate-action-interpreter

Every date, term, option, and entitlement figure in the interpretation must cite one of
the sources below, ranked. See the shared platform services in
[`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Depository / transfer-or-paying-agent **official notice** (DTC/DTCC, agent) | Event type, mandatory/voluntary status, key dates, option terms | Read-only (post-trade/clearing) |
| 2 | Issuer **offering document / official announcement** (prospectus, offer to purchase, 8-K) | Governing terms, ratios, per-share rates, conditions | Read-only (document-intelligence / approved-source retrieval) |
| 3 | **Reference/market data** vendor scrub | Confirmation of terms/dates; security identity | Read-only |
| 4 | Custody **books-and-records** | Eligible position (quantity) and as-of date | Read-only (portfolio-accounting/custody) |
| 5 | User-provided screenshot/summary | Only when 1–4 unavailable; must be labeled unverified | Read-only |

Never let a user assertion override the official notice. If sources conflict (e.g., vendor
scrub disagrees with the depository notice), present both with citations and stop for
operations review.

## Citation format

Each date, term, and entitlement carries a citation of the form `{system}:{ref}@{date}` —
e.g. `depository:DTC CA #2026-0442;opt=002@2026-05-28`,
`issuer:offer-to-purchase p12,s3@2026-05-27`, or
`custody:acct=****7788;CUSIP037833100@2026-06-10`. The machine-readable output stores the
citation per entitlement and per option; the narrative references them inline where a
figure or date is stated.

## Freshness / effective dates

- Corporate-action notices are **versioned**; always interpret the **latest official
  version**. A superseded or amended notice is flagged, and the replaced version is not
  used.
- Entitlement is computed on the **record-date** position; a differing position as-of is
  flagged for confirmation.
- For voluntary / mandatory-with-options events, the **election deadline** must be stated;
  a passed deadline is surfaced explicitly (it does not change what the skill does — the
  skill still only explains).

## Least-privilege operations (deployment)

- `ca_notice.read(event_id)` → normalized notice (event type, dates, terms, options).
- `refdata.security(instrument_id)` → security identity for confirmation.
- `positions.read(account_id, as_of=record_date)` → eligible quantity (bounded page size).
All read-only, deterministic schemas, durable `interpretation_id`, below the fixed timeout.
The skill binds **no** election / instruction / write operation.
