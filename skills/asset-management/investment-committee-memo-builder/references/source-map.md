# Source Map — investment-committee-memo-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Financial model** (LBO / three-statement / DCF outputs) | Entry/exit, returns, leverage, tie-outs | Read-only |
| 2 | **Diligence materials** (VDR: QoE, legal, commercial, tax) | Thesis, risks, mitigants, structure terms | Read-only |
| 3 | **Transaction documents** (SPA / term sheet / credit agreement) | Structure, conditions precedent, covenants | Read-only |
| 4 | **Market & company data** (comps, multiples, pricing) | Valuation vs. peers, market context | Read-only |
| 5 | **Approved research** (controlled content library) | Sector/thesis support (owner + effective date) | Read-only |
| 6 | **Portfolio context** (fund NAV, exposures, limits) | Sizing, concentration, portfolio fit | Read-only |
| 7 | Approved **IC memo template** + limit config (versioned) | Section contract, concentration limits | Read-only |

The model is the system of record for figures; the memo must **tie out** to it, never restate
looser numbers. Diligence and transaction documents are authoritative for facts and terms.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `model:meridian-lbo@v7`, `vdr:QoE-final@2026-07-02`,
`data:sector-comps@2026-07-08`, `research:industrials-outlook@2026-Q2`,
`portfolio:fund-III-exposure@2026-07-15`. Every material figure and claim carries one.

## Freshness / effective dates

- Model, comps, and portfolio exposures must be read **fresh** for the IC date; a stale NAV
  or comp set silently mis-sizes the position or mis-values the entry.
- Approved research and the memo template/limit config are **versioned contracts**; record
  the version used on every draft so the memo is reproducible.
- Market/research inputs must be **approved** in the controlled content library; an
  unapproved external source is blocked (its dependent claims fail as unapproved).

## Conflict handling

When the model, diligence, and market data disagree on a figure, cite all and surface the
gap as a decision question — do **not** silently pick one. The model figure governs the
structure/returns tie-outs; a diligence adjustment (e.g. QoE normalization) is disclosed
explicitly, not folded in without a citation.

## Least-privilege operations (deployment)

- `model.read(model_id, version)`, `vdr.read(doc_id)`, `txndocs.read(doc_id)` — read-only.
- `market.comps(sector, as_of)`, `research.get(topic, version)` (approved only) — read-only.
- `portfolio.exposure(fund_id, as_of)`, `config.get('ic-limits'|'ic-template', version)` — read-only.

No mutation from this skill. It never writes to the deal/IC system of record, never records
the committee decision, and never sends or circulates the memo — a human does that after
review. Bundled `scripts/` operate only on the documented JSON schema and de-identified
fixtures under `evals/files/`; they open no network connections.
