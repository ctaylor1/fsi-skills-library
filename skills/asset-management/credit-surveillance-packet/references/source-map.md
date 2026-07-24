# Source Map — credit-surveillance-packet

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filings / financial statements** (10-K/10-Q, MD&A) | EBITDA, debt, cash, interest, capex → leverage/coverage/liquidity | Read-only |
| 2 | **Credit agreement / indenture** (controlled documents) | Maturity schedule; which covenant items exist and changed | Read-only |
| 3 | **Rating-agency reports** | Reported agency rating + outlook (and prior) | Read-only |
| 4 | **Market data** (bond OAS / CDS) | Current vs prior credit spread | Read-only |
| 5 | **Internal credit model / spreading** (deterministic computation service) | Recompute and tie out leverage/coverage ratios | Read-only |
| 6 | **Reference data / security master** | Issuer/instrument resolution | Read-only |
| 7 | Approved **packet template** + metric/threshold config (versioned) | Section contract, tolerances, disclosure thresholds | Read-only |

The **filing** is the system of record for the raw financials; computed ratios must **tie out**
to those inputs and never restate a looser number. The **credit agreement** is authoritative for
the maturity schedule and for *which* covenant items exist and changed — full covenant-term
extraction and interpretation are handed off (see [handoffs.md](handoffs.md)).

## Citation format

`{system}:{ref}@{as-of/version}` — e.g. `filing:10Q-2026Q2@2026-06-30`,
`creditagr:credit-agreement-A3@2026-05-15`, `rating:AgencyA-2026-06@2026-06-20`,
`market:issuer-oas-5y@2026-06-30`, `config:credit-surv@v2026.07`. Every material figure and
claim carries one; ratings always cite the rating-agency source (never an internal derivation).

## Freshness / effective dates

- Financials, spreads, and rating reports must be read **fresh** for the surveillance as-of
  date; a stale spread or an outdated rating misstates the issuer's current standing.
- The metric/threshold config and packet template are **versioned contracts**; record the
  version used on every packet so the metrics and disclosure thresholds are reproducible.
- Market and rating-agency inputs must be **approved** in the controlled content library; an
  unapproved external source is blocked (its dependent claims fail as unapproved).

## Conflict handling

When a filing, an internal spread, and a vendor value disagree on a figure, cite all and
surface the gap in the citations/evidence section — do **not** silently pick one. The filing
governs the leverage/coverage tie-outs; a normalization adjustment is disclosed explicitly with
a citation, never folded in silently.

## Least-privilege operations (deployment)

- `filing.read(issuer_id, period)`, `creditagr.read(doc_id)` — read-only.
- `rating.read(issuer_id, as_of)`, `market.spread(instrument, as_of)` (approved only) — read-only.
- `model.spread(issuer_id, period)` (recompute ratios), `refdata.resolve(issuer_id)` — read-only.
- `config.get('credit-surv-template'|'credit-surv-metrics', version)` — read-only.

No mutation from this skill. It never writes to the research/position system of record, never
assigns a rating, never records a thesis or position change, and never sends or delivers the
packet — a human does that after review. Bundled `scripts/` operate only on the documented JSON
schema and de-identified fixtures under `evals/files/`; they open no network connections.
