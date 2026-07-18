# Source Map — premium-quote-comparator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Producer / rating systems** — carrier quotes of record | Premium, term, coverages, limits, deductibles, fees, endorsements | Read-only |
| 2 | **Document intelligence** — quote PDFs / ACORD forms | Extract quote fields when only a document is supplied; cite page/field | Read-only |
| 3 | **Policy administration** | Coverage-code taxonomy, endorsement/form catalog for normalization | Read-only |
| 4 | **Actuarial / reference data** | Currency, FX, jurisdiction minimums, coverage-code crosswalk | Read-only |
| 5 | Normalization **config** (versioned) | Payment-frequency multipliers, fee annualization, coverage crosswalk | Read-only |

The **carrier's quote of record** is authoritative for that carrier's numbers. Never
substitute a customer recollection or a marketing figure for the quoted amount. If an
extracted document and a rating-system value conflict, cite both and flag for the reviewer.

## Citation format

`quote:{source_ref}@{as_of}` — e.g. `quote:carrier=SafeHarbor;quoteid=Q-A@2026-07-15`. Every
normalized figure and every itemized difference cites the quote(s) it came from.

## Freshness / effective dates

- Quotes are **time-bound**: record each quote's `as_of` and note that premiums expire and
  may re-rate. A comparison is valid only for the effective dates of its quotes.
- Config (frequency multipliers, fee treatment, coverage crosswalk) is a **versioned
  contract**; the output records the `config_version` used so a comparison is reproducible.
- Currency and jurisdiction are part of comparability — different currencies or state
  minimums are surfaced as flags, not silently reconciled.

## Least-privilege operations (deployment)

- `producer.quotes(risk_type, quote_ids)` → quote rows with coverages, limits, deductibles, fees.
- `docintel.extract(document_id)` → fielded quote data with page citations.
- `refdata.coverage_crosswalk(risk_type)` → normalized coverage codes/names.
- `config.get('quote-normalize', version)` → multipliers + crosswalk.
All read-only, deterministic, durable `comparison_id`, below the fixed timeout; page long
quote sets as resumable stages.
